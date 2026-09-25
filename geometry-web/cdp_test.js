/* CDP 驅動 headless Chrome 實測物件畫布互動 */
const { spawn } = require("child_process");
/* 預設為 Windows 的 Chrome；下列環境變數可覆寫，用於在 WSL/Linux 內整條跑：
     GEOMETRY_CHROME         chrome 執行檔路徑（Linux 下通常是 google-chrome）
     GEOMETRY_CHROME_PROFILE --user-data-dir 的位置
     GEOMETRY_CHROME_FLAGS   追加旗標，空白分隔（在 WSL 內以 root 跑需要 --no-sandbox）
   不設時行為與先前完全相同。 */
const CHROME = process.env.GEOMETRY_CHROME || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PROFILE = process.env.GEOMETRY_CHROME_PROFILE || "C:\\tmp\\cdp-profile";
const EXTRA_FLAGS = (process.env.GEOMETRY_CHROME_FLAGS || "").split(" ").filter(Boolean);
const PORT = 9333;

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", `--remote-debugging-port=${PORT}`,
  "--window-size=1400,900", `--user-data-dir=${PROFILE}`, ...EXTRA_FLAGS, "about:blank"
]);

const sleep = ms => new Promise(r => setTimeout(r, ms));
let ws, mid = 0, pending = {};

/* ✓/✗ 計數：所有印出的判定一律計入，exit code 依此決定。 */
let passN = 0, failN = 0;
let excN = 0;            /* Runtime.exceptionThrown 計數(BF2 驗收用) */
const _log = console.log;
console.log = (...args) => {
  const s = args.join(" ");
  passN += (s.match(/✓/g) || []).length;
  failN += (s.match(/✗/g) || []).length;
  _log(...args);
};

async function connect() {
  for (let i = 0; i < 40; ++i) {
    try {
      const list = await fetch(`http://127.0.0.1:${PORT}/json`).then(r => r.json());
      const page = list.find(t => t.type === "page");
      if (page) {
        ws = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
        ws.onmessage = ev => {
          const m = JSON.parse(ev.data);
          if (m.id && pending[m.id]) { pending[m.id](m); delete pending[m.id]; }
          else if (m.method === "Runtime.consoleAPICalled")
            console.log("[console]", m.params.args.map(a => a.value ?? a.description).join(" "));
          else if (m.method === "Runtime.exceptionThrown") {
            excN++;
            console.log("[EXCEPTION]", JSON.stringify(m.params.exceptionDetails.exception?.description || m.params));
          }
        };
        return;
      }
    } catch {}
    await sleep(250);
  }
  throw new Error("no CDP");
}
function send(method, params = {}) {
  return new Promise(res => { const id = ++mid; pending[id] = res; ws.send(JSON.stringify({ id, method, params })); });
}
async function eval_(expr) {
  const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.result.exceptionDetails) return { __err: r.result.exceptionDetails.exception?.description };
  return r.result.result.value;
}
async function click(x, y) {
  for (const [type, btn] of [["mousePressed", "left"], ["mouseReleased", "left"]])
    await send("Input.dispatchMouseEvent", { type, x, y, button: btn, clickCount: 1 });
}
async function dblclick(x, y) {
  for (const n of [1, 2])
    for (const type of ["mousePressed", "mouseReleased"])
      await send("Input.dispatchMouseEvent", { type, x, y, button: "left", clickCount: n });
}
async function drag(x0, y0, x1, y1, steps = 6) {
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: x0, y: y0, button: "left", clickCount: 1 });
  for (let i = 1; i <= steps; ++i)
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x0 + (x1 - x0) * i / steps, y: y0 + (y1 - y0) * i / steps, button: "left" });
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: x1, y: y1, button: "left", clickCount: 1 });
}

(async () => {
  await connect();
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Page.navigate", { url: process.env.GEOMETRY_TEST_URL || "http://localhost:8765/" });
  await sleep(2500);
  if (!process.env.GEOMETRY_UI_REVIEW_ONLY && !process.env.GEOMETRY_REPAIR_ONLY) {
  /* 清世界 + 建一個乾淨的測試場：一片游離面、一個空容器 */
  await eval_(`api("line reset")`);
  await eval_(`api("line boundary 1 outline 0,0 4000,0 4000,3000 0,3000")`);
  await eval_(`api("line canvas-pos boundary 1 60 60")`);
  await sleep(500);

  console.log("=== 1. Phase 1 版面檢查點(§6) ===");
  /* (a) #app 三列:56 / 1fr / 32 */
  const rows = await eval_(`(()=>{const app=document.getElementById("app");
    const kids=[...app.children];return {n:kids.length,
      cls:kids.map(k=>k.className.split(" ")[0]).join(","),
      h:kids.map(k=>Math.round(k.getBoundingClientRect().height))}})()`);
  console.log("app rows:", JSON.stringify(rows),
    rows.n === 3 && rows.h[0] === 56 && rows.h[2] === 32 ? "✓ 三列殼" : "✗");
  /* (b) .workspace 三欄:左 260 / 中 1fr / 右 320 */
  const cols = await eval_(`(()=>{const w=document.querySelector(".workspace");
    const k=[...w.children];return {n:k.length,
      w:k.map(c=>Math.round(c.getBoundingClientRect().width))}})()`);
  console.log("workspace cols:", JSON.stringify(cols),
    cols.n === 3 && cols.w[0] === 260 && cols.w[2] === 320 ? "✓ 三欄" : "✗");
  /* (c) topbar 子層序:brand → tool-group → top-actions */
  const tb = await eval_(`[...document.querySelector(".topbar").children].map(c=>c.className.split(" ")[0]).join(",")`);
  console.log("topbar order:", tb,
    tb === "brand,tool-group,top-actions" ? "✓ 頂列順序" : "✗");
  /* (d) #ocv 在 #canvasViewport 內且同大小(誤差≤2px) */
  const fit = await eval_(`(()=>{const v=document.getElementById("canvasViewport").getBoundingClientRect();
    const o=document.getElementById("ocv").getBoundingClientRect();
    return {dv:Math.abs(v.left-o.left)+Math.abs(v.top-o.top),
            ds:Math.abs(v.width-o.width)+Math.abs(v.height-o.height)}})()`);
  console.log("ocv fit:", JSON.stringify(fit),
    fit.dv <= 2 && fit.ds <= 2 ? "✓ ocv 鋪滿 viewport" : "✗");
  /* (e) #status 與 #cmd 都在 .statusbar 裡 */
  const sb = await eval_(`(()=>{const sb=document.querySelector(".statusbar");
    return !!(sb.querySelector("#status") && sb.querySelector("#cmd"))})()`);
  console.log("statusbar:", sb ? "✓ status/cmd 在狀態列" : "✗");
  /* (f) A1 防溢出:.top-actions 右緣 ≤ viewport、左緣 > .tool-group 右緣(1382 與 1160) */
  for (const w of [1382, 1160, 900, 680, 600]) {
    await send("Emulation.setDeviceMetricsOverride",
      { width: w, height: 804, deviceScaleFactor: 1, mobile: false });
    await sleep(350);
    const ov = await eval_(`(()=>{
      const ta=document.querySelector(".top-actions").getBoundingClientRect();
      const tg=document.querySelector(".tool-group").getBoundingClientRect();
      return {taR:Math.round(ta.right),taL:Math.round(ta.left),tgR:Math.round(tg.right),iw:innerWidth}})()`);
    console.log(`防溢出@${w}:`, JSON.stringify(ov),
      ov.taR <= ov.iw && ov.taL > ov.tgR ? "✓" : "✗");
  }
  await send("Emulation.setDeviceMetricsOverride",
    { width: 1382, height: 804, deviceScaleFactor: 1, mobile: false });
  await sleep(300);
  /* (g) S2 結構:搜尋在左欄;fileMenu 含四鈕;viewSwitch 含 btnObj */
  const s2 = await eval_(`({
    searchInSide: !!document.querySelector(".sidebar-left #searchInput"),
    fileKids: ["btnOpen","btnDatums","btnEx","btnClear"].every(id=>
      document.getElementById("fileMenu").contains(document.getElementById(id))),
    vsHasObj: document.getElementById("viewSwitch").contains(document.getElementById("btnObj")),
    zoomInCtl: document.querySelector(".canvas-controls").contains(document.getElementById("btnZoom")),
    kbd: document.querySelectorAll(".tool-group kbd").length
  })`);
  console.log("S2 結構:", JSON.stringify(s2),
    s2.searchInSide && s2.fileKids && s2.vsHasObj && s2.zoomInCtl && s2.kbd === 2 ? "✓" : "✗");
  /* (h) A2 清單樣式:.row-copy > strong + small */
  await eval_(`renderObjects()`); await sleep(400);
  const rowCk = await eval_(`(()=>{const r=document.querySelector(".object-row .row-copy strong");
    return r ? getComputedStyle(r).fontSize : null})()`);
  console.log("清單樣式 row-copy strong:", rowCk,
    rowCk && parseFloat(rowCk) >= 12 ? "✓" : "✗");
  /* (i) E8:800px 寬進面內工作區,工具列仍有不少於 5 顆可見鈕 */
  await send("Emulation.setDeviceMetricsOverride",
    { width: 800, height: 600, deviceScaleFactor: 1, mobile: false });
  await eval_(`enterFocus("face",1)`); await sleep(600);
  const e8 = await eval_(`[...document.querySelectorAll("#faceWorkspaceTools .workspace-tool")]
    .filter(b=>b.getBoundingClientRect().width>0).length`);
  console.log("E8 800px 面內工具鈕:", e8, e8 >= 5 ? "✓" : "✗");
  await eval_(`leaveFocus()`); await sleep(300);
  await send("Emulation.setDeviceMetricsOverride",
    { width: 1382, height: 804, deviceScaleFactor: 1, mobile: false });
  await sleep(300);
  /* 截圖存檔 */
  const shot = await send("Page.captureScreenshot", { format: "png" });
  require("fs").mkdirSync("docs/screens", { recursive: true });
  const screenshotPath = process.env.GEOMETRY_TEST_SCREENSHOT || "docs/screens/phase1-shell.png";
  require("fs").writeFileSync(screenshotPath, Buffer.from((shot.result && shot.result.data) || "", "base64"));
  console.log("screenshot:", screenshotPath);
  console.log("初始:oc.on=", await eval_(`oc.on`),
    "ocv.hidden=", await eval_(`document.getElementById("ocv").hasAttribute("hidden")`),
    "cv.hidden=", await eval_(`document.getElementById("cv").hasAttribute("hidden")`),
    "cards=", await eval_(`document.querySelectorAll(".ocard").length`));

  console.log("=== 2. 三視圖覆層開/關 ===");
  const btnRect = await eval_(`(()=>{const r=document.getElementById("btnObj").getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
  await click(btnRect.x, btnRect.y);
  await sleep(1000);
  const v3on = await eval_(`({cv:document.getElementById("cv").hasAttribute("hidden"),
    vt:document.getElementById("viewToolbar").hasAttribute("hidden"),on:oc.on,
    world:document.getElementById("world").childElementCount})`);
  console.log("view3 open:", JSON.stringify(v3on),
    !v3on.cv && !v3on.vt && !v3on.on ? "✓ 三視圖開啟" : "✗");
  await click(btnRect.x, btnRect.y);
  await sleep(300);
  console.log("view3 repeated selection:", !(await eval_(`oc.on`)) ? "✓ 維持三視圖" : "✗");
  const canvasButton = await eval_(`(()=>{const r=document.getElementById("btnCanvasView").getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
  await click(canvasButton.x, canvasButton.y);
  await sleep(700);
  const v3off = await eval_(`({cv:document.getElementById("cv").hasAttribute("hidden"),on:oc.on})`);
  console.log("view3 close:", JSON.stringify(v3off),
    v3off.cv && v3off.on ? "✓ 返回物件畫布" : "✗");
  console.log("cards:", await eval_(`document.querySelectorAll(".ocard").length`));

  console.log("=== 3. 拖曳空白處（pan） ===");
  const ocvRect = await eval_(`JSON.stringify(document.getElementById("ocv").getBoundingClientRect())`);
  console.log("ocv rect:", ocvRect);
  const panBefore = await eval_(`({x:oc.panX,y:oc.panY})`);
  /* 找 ocv 內避開卡片的空白點 */
  const panPt = await eval_(`(()=>{
    const r = document.getElementById("ocv").getBoundingClientRect();
    const boxes = [...document.querySelectorAll(".ocard")].map(c => c.getBoundingClientRect());
    for (let y = r.top + 60; y < r.bottom - 60; y += 40)
      for (let x = r.left + 60; x < r.right - 60; x += 40)
        if (boxes.every(b => x < b.left - 20 || x > b.right + 20 ||
                             y < b.top - 20 || y > b.bottom + 20))
          return {x, y};
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  console.log("pan pt:", JSON.stringify(panPt));
  await drag(panPt.x, panPt.y, panPt.x + 80, panPt.y + 50);
  const panAfter = await eval_(`({x:oc.panX,y:oc.panY})`);
  console.log("pan:", JSON.stringify(panBefore), "->", JSON.stringify(panAfter),
              panBefore.x !== panAfter.x ? "✓ 平移有效" : "✗ 平移無效");

  console.log("=== 4. 點「＋面·矩形」再拉矩形（避開卡片的空白區） ===");
  await eval_(`document.getElementById("btnNewRect").click()`);
  await sleep(200);
  const facesBefore = await eval_(`oc.faces.length`);
  /* 找出空白處：避開所有卡片的螢幕範圍 */
  const empty = await eval_(`(()=>{
    const r = document.getElementById("ocv").getBoundingClientRect();
    const boxes = [...document.querySelectorAll(".ocard")].map(c => c.getBoundingClientRect());
    for (let y = r.top + 60; y < r.bottom - 60; y += 30)
      for (let x = r.left + 60; x < r.right - 160; x += 30)
        if (boxes.every(b => x < b.left - 40 || x > b.right + 160 ||
                             y < b.top - 40 || y > b.bottom + 110))
          return {x, y};
    return {x: r.right - 200, y: r.bottom - 150};
  })()`);
  console.log("empty pt:", JSON.stringify(empty));
  /* 探針：看 pointerdown 是否真的送達 ocv，以及 target/button 是什麼 */
  await eval_(`window.__pd = null; ocv.addEventListener("pointerdown",
    e => window.__pd = { b: e.button, t: e.target.tagName, cls: e.target.getAttribute("class"),
                         x: e.clientX, y: e.clientY }, true)`);
  console.log("elementFromPoint:", await eval_(
    `(()=>{const e=document.elementFromPoint(${empty.x},${empty.y});return e?e.tagName+"#"+e.id+"."+(e.getAttribute("class")||""):"null"})()`));
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: empty.x, y: empty.y, button: "left", clickCount: 1 });
  await sleep(150);
  console.log("probe:", await eval_(`JSON.stringify(window.__pd)`));
  console.log("after down: drawTool=", await eval_(`oc.drawTool`),
              "rect=", await eval_(`JSON.stringify(oc.rect)`),
              "card=", await eval_(`JSON.stringify(oc.card)`),
              "pan=", await eval_(`JSON.stringify(oc.pan)`));
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: empty.x + 70, y: empty.y + 45, button: "left" });
  await sleep(150);
  console.log("after move: rect=", await eval_(`JSON.stringify(oc.rect)`));
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: empty.x + 140, y: empty.y + 90, button: "left", clickCount: 1 });
  await sleep(1500);
  const facesAfter = await eval_(`oc.faces.length`);
  console.log("faces:", facesBefore, "->", facesAfter, facesAfter > facesBefore ? "✓ 建面成功" : "✗ 建面失敗");
  console.log("status:", await eval_(`document.getElementById("status").textContent`));
  console.log("cards:", await eval_(`document.querySelectorAll(".ocard").length`));

  console.log("=== 5. 拖卡片（應寫 canvas-pos，不進入） ===");
  const cardBox = await eval_(`(()=>{
    const c = document.querySelector(".ocard");
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + 20};
  })()`);
  if (cardBox) {
    const posBefore = await eval_(`JSON.stringify(oc.faces.map(f=>[f.id,f.cx,f.cy]))`);
    await drag(cardBox.x, cardBox.y, cardBox.x + 120, cardBox.y + 60);
    await sleep(1200);
    const posAfter = await eval_(`JSON.stringify(oc.faces.map(f=>[f.id,f.cx,f.cy]))`);
    console.log("card pos:", posBefore, "->", posAfter,
                posBefore !== posAfter ? "✓ 拖卡片有效" : "✗ 拖卡片無效");
  }

  console.log("=== 6. 點卡=選取(檢視器);雙擊=進入面編輯 ===");
  const cardPt = await eval_(`(()=>{
    const cards = [...document.querySelectorAll(".ocard")];
    const c = cards[cards.length - 1];   /* 最後建的游離面 */
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  console.log("card pt:", JSON.stringify(cardPt));
  if (cardPt) {
    await click(cardPt.x, cardPt.y);
    await sleep(600);
    const sel = await eval_(`JSON.stringify(oc.sel)`);
    console.log("click sel:", sel,
      JSON.parse(sel) ? "✓ 單擊選取" : "✗",
      "| inspector hidden:", await eval_(`document.getElementById("inspectorContent").hidden`));
    console.log("focus(應為 null):", await eval_(`JSON.stringify(oc.focus)`));
    await dblclick(cardPt.x, cardPt.y);
    await sleep(1000);
    console.log("focus:", await eval_(`JSON.stringify(oc.focus)`));
    console.log("status:", await eval_(`document.getElementById("status").textContent`));
  }

  console.log("=== 7. 面編輯：拖一個頂點 ===");
  console.log("workspace open:", await eval_(
    `!document.getElementById("objectWorkspace").hidden`));
  const vtx = await eval_(`(()=>{
    if (!oc.focus || oc.focus.t !== "face" || !oc.edit) return null;
    const e = oc.edit, loops = oc.bmap[e.bid];
    if (!loops || !loops[0].verts.length) return null;
    const p = loops[0].verts[0];
    const r = document.getElementById("faceEditorSvg").getBoundingClientRect();
    return { x: r.left + p[0]*fe.zoom + fe.panX, y: r.top + p[1]*fe.zoom + fe.panY };
  })()`);
  if (vtx) {
    const vBefore = await eval_(`JSON.stringify(oc.bmap[oc.edit.bid][0].verts[0])`);
    await drag(vtx.x, vtx.y, vtx.x + 60, vtx.y + 40);
    await sleep(1200);
    const vAfter = await eval_(`JSON.stringify(oc.bmap[oc.edit.bid][0].verts[0])`);
    console.log("vert0:", vBefore, "->", vAfter,
                vBefore !== vAfter ? "✓ 頂點編輯有效" : "✗ 頂點編輯無效");
    console.log("status:", await eval_(`document.getElementById("status").textContent`));
  } else console.log("沒進入面編輯，跳過");

  console.log("=== 8. Esc 返回世界 ===");
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(500);
  console.log("focus after Esc:", await eval_(`JSON.stringify(oc.focus)`));

  console.log("=== 9. 「＋空間」建空容器 ===");
  const spBefore = await eval_(`oc.spaces.length`);
  await eval_(`document.getElementById("btnNewSpace").click()`);
  await sleep(1500);
  const spAfter = await eval_(`oc.spaces.length`);
  console.log("spaces:", spBefore, "->", spAfter, spAfter > spBefore ? "✓ 空間建立成功" : "✗ 失敗");
  console.log("status:", await eval_(`document.getElementById("status").textContent`));
  console.log("newid:", await eval_(`api("newid").then(r=>JSON.stringify(r))`));

  console.log("=== 9b. 點空間卡進入成員層 ===");
  const spPt = await eval_(`(()=>{
    const c = [...document.querySelectorAll(".ocard")].find(c => c.dataset.kind === "space");
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  if (spPt) {
    await dblclick(spPt.x, spPt.y);
    await sleep(800);
    console.log("focus:", await eval_(`JSON.stringify(oc.focus)`),
                await eval_(`oc.focus && oc.focus.t === "space" ? "✓" : "✗"`));
    await eval_(`leaveFocus()`); await sleep(300);
  }

  console.log("=== 9c. 「＋面·多邊形」建面卡→面內畫外環(GEO-186 b) ===");
  /* GEO-186(b,2026-09-24 拍板):P 不再是畫布上的 mm 繪圖工具——同一張畫布混用
     「mm 繪圖」與「固定尺寸卡片排版」兩套座標是 GEO-187「找不到卡片」的根因。
     按一下 = 建預設外環的面卡 → 直接進入該面工作區並啟用「重畫外環」,
     在面內以實際 mm 逐點畫。面內繪圖機制另有 §P35/P36 專門斷言。 */
  await eval_(`oc.zoom=1;oc.panX=0;oc.panY=0;ocApply()`);
  const fb2 = await eval_(`oc.faces.length`);
  await eval_(`document.getElementById("btnNewPoly").click()`);
  await sleep(900);
  const fa2 = await eval_(`oc.faces.length`);
  const ws9 = await eval_(`({focus:oc.focus, tool:fe.tool})`);
  console.log("faces:", fb2, "->", fa2, fa2 > fb2 ? "✓ 建面成功" : "✗ 失敗",
    "| 自動進面內:", ws9.focus && ws9.focus.t === "face" ? "✓" : "✗",
    "| 重畫外環就緒:", ws9.tool === "redraw" ? "✓" : "✗ " + ws9.tool);
  console.log("status:", await eval_(`document.getElementById("status").textContent`));
  /* Esc 回物件畫布,讓 9d 在畫布上驗 undo/redo(單次 undo 移除整個建面交易) */
  for (const type of ['keyDown','keyUp'])
    await send('Input.dispatchKeyEvent', { type, key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await sleep(500);
  console.log("Esc 回畫布:", (await eval_(`oc.focus`)) === null ? "✓" : "✗");

  console.log("=== 9d. Ctrl+Z 復原 / Ctrl+Y 重做 ===");
  /* §5.A.1.15 已知風險,實測後更新(2026-09-22):新 objEmitFace 閉合當下直接算 bbox
     左上送 canvas-pos，不再落入 renderObjects() 的 homeless 自動排格分支；而
     `canvas-pos` 本身不進 undo 歷史(DOM-CONTRACT.md「canvas-pos 是展示中繼資料，
     不進歷史」/ canvas_test.js U1/L1 既有斷言)，所以「建 boundary」+「送 canvas-pos」
     不再是兩筆各自要復原的交易——實測(本檔案 2026-09-22 一併驗證,見下方單步 undo/redo)
     單次 Ctrl+Z 就讓面連同座標一起消失、單次 Ctrl+Y 就完整還原。HEAD 舊註解「undo 兩次
     才回到面消失」的假設在這版 objEmitFace 下不成立,依規則更新。
     不测「再按一次應不變」:§9 建立過的空間也在同一份 undo 歷史裡,多按一次 undo/redo
     會動到空間那筆交易(不影響 oc.faces.length,但也不是嚴格「無事發生」),用 dump 比對
     世界整體是否精確復原比只看 face 數更準確、也更貼近規格意圖。 */
  const facesN = `oc.faces.length`;
  const fPreUndo = await eval_(facesN);
  const dumpPreUndo = (await eval_(`api("dump").then(r=>r.text)`));
  const key = async (k, code, vk) => {
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, modifiers: 2, windowsVirtualKeyCode: vk });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, modifiers: 2, windowsVirtualKeyCode: vk });
  };
  await key("z", "KeyZ", 90); await sleep(800);
  const fU1 = await eval_(facesN);
  const st1 = await eval_(`document.getElementById("status").textContent`);
  console.log("undo1 api faces:", await eval_(`api("objects").then(r=>r.faces.length)`));
  console.log("undo×1(單步移除建面+落點):", fPreUndo, "->", fU1,
              fU1 === fPreUndo - 1 ? "✓ undo 有效" : "✗", "|", st1);
  await key("y", "KeyY", 89); await sleep(800);
  const fR1 = await eval_(facesN);
  const dumpAfterRedo = (await eval_(`api("dump").then(r=>r.text)`));
  console.log("redo×1(單步還原):", fU1, "->", fR1, fR1 === fPreUndo ? "✓ redo 有效" : "✗");
  console.log("redo 後世界與 undo 前逐字相同:", dumpAfterRedo === dumpPreUndo ? "✓" : "✗");

  console.log("=== 9e. contains 連線(edgeGroup) ===");
  /* 空間成員必須是有承載面的邊界面:先用 surface 建地板+牆(區間一致),
     再用 #cmd 送 space 1 boundary 10 11 → edgeGroup 應有 2 條邊 */
  const cmdLine = async t => {
    await eval_(`(()=>{const c=document.getElementById("cmd");
      c.value=${JSON.stringify("X")}.replace("X",${JSON.stringify(t)});
      c.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter",bubbles:true}))})()`);
    await sleep(600);
  };
  await cmdLine("surface 10 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000");
  await cmdLine("surface 11 origin 0 0 0 u +x v +z outline 0,0 4000,0 4000,2500 0,2500");
  await cmdLine("space 1 boundary 10 11");
  await sleep(1200);
  console.log("space members:", await eval_(
    `api("objects").then(r=>JSON.stringify(r.spaces.map(s=>[s.id,s.members])))`));
  const edgeN = await eval_(`document.querySelectorAll("#edgeGroup .edge-path").length`);
  console.log("edges:", edgeN, edgeN === 2 ? "✓ contains 邊×2" : "✗");
  console.log("edge labels:", await eval_(
    `[...document.querySelectorAll("#edgeLabelLayer .edge-label")].map(t=>t.textContent).join(",")`));

  console.log("=== 9f. 搜尋過濾 ===");
  const cardsAll = await eval_(`document.querySelectorAll(".ocard").length`);
  await eval_(`(()=>{const si=document.getElementById("searchInput");
    si.value="面 1";si.dispatchEvent(new Event("input",{bubbles:true}))})()`);
  await sleep(600);
  const cardsQ = await eval_(`document.querySelectorAll(".ocard").length`);
  console.log("cards:", cardsAll, "->", cardsQ, cardsQ === 1 ? "✓ 搜尋只剩 1 張卡" : "✗");
  const listQ = await eval_(`document.querySelectorAll("#objectList .object-row").length`);
  console.log("list rows:", listQ, listQ === 1 ? "✓ 清單同步過濾" : "✗");
  /* 清掉搜尋 */
  await eval_(`(()=>{const si=document.getElementById("searchInput");
    si.value="";si.dispatchEvent(new Event("input",{bubbles:true}))})()`);
  await sleep(400);

  /* ================= Phase 3：面內工作區 ================= */
  console.log("=== P3-1. 已放置面（天花 surface 20）進入工作區 ===");
  await cmdLine("surface 20 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
  await sleep(800);
  const card20 = await eval_(`(()=>{
    const c = document.querySelector('.ocard[data-id="20"]');
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  console.log("card20:", JSON.stringify(card20));
  if (card20) {
    await dblclick(card20.x, card20.y);
    await sleep(1000);
    console.log("focus:", await eval_(`JSON.stringify(oc.focus)`),
      await eval_(`oc.focus && oc.focus.t==="face" && oc.focus.id===20 ? "✓ 進入面 20" : "✗"`));
    console.log("workspace:", await eval_(
      `!document.getElementById("objectWorkspace").hidden ? "✓ 開啟" : "✗ 未開啟"`));
  }

  console.log("=== P3-2. 參考線：水平拖 → guide <n> 20 v <off> ===");
  await eval_(`document.querySelector('[data-face-tool="guide"]').click()`);
  await sleep(300);
  const feCtr = await eval_(`(()=>{
    const r = document.getElementById("faceEditorViewport").getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  await drag(feCtr.x - 80, feCtr.y, feCtr.x + 80, feCtr.y + 4);   /* 水平拖 → v 線 */
  await sleep(900);
  const dump1 = await eval_(`api("dump").then(r=>r.text)`);
  const rawGuide = /^guide /m.test(dump1);
  console.log("無具名規格或鄰近引用的自由拖放拒絕:", !rawGuide ? "✓" : "✗");
  await eval_(`(async()=>{await api("line spec 面內線 1500"); await api("line guide 1 20 u spec:面內線"); await feLoadGuides();drawFaceEditor()})()`);
  const gMatch = await eval_(`api('references').then(r=>r.guides.find(g=>g.surface===20))`);
  console.log("引用建線:", gMatch?.expression === 'spec:面內線' && gMatch.off === 1500 ? "✓" : "✗");

  console.log("=== P3-3. 開口：拉矩形 → boundary 20 loops=2 ===");
  await eval_(`document.querySelector('[data-face-tool="hole"]').click()`);
  await sleep(200);
  const holeBox = await eval_(`(()=>{
    const r = document.getElementById("faceEditorSvg").getBoundingClientRect();
    const toScr = p => ({x: r.left + p[0]*fe.zoom + fe.panX,
                         y: r.top + p[1]*fe.zoom + fe.panY});
    const a = toScr([500, 500]), b = toScr([1200, 1000]);
    return {a, b};
  })()`);
  await drag(holeBox.a.x, holeBox.a.y, holeBox.b.x, holeBox.b.y);
  await sleep(900);
  const loopN = await eval_(`api("boundary 20").then(r=>r.ok ? r.loops.length : -1)`);
  console.log("loops:", loopN, loopN === 2 ? "✓ 開口成功" : "✗");

  console.log("=== P3-4. 投影面板：天花面 → 恰一個 data-view=2 ===");
  await eval_(`document.getElementById("projToggle").click()`);
  await sleep(1000);
  const projN2 = await eval_(
    `document.querySelectorAll('#projViews [data-view="2"]').length`);
  const projAll = await eval_(
    `document.querySelectorAll('#projViews [data-view]').length`);
  console.log("proj groups:", projAll, "view2:", projN2,
    projN2 === 1 && projAll === 1 ? "✓ 只顯示仰視" : "✗");

  console.log("=== P3-5. 非法編輯 → toast + boundary 不變 ===");
  const bSnap = await eval_(
    `api("boundary 20").then(r=>JSON.stringify(r.loops))`);
  await cmdLine("boundary 20 outline 0,0 4000,0 4000,3000 1500,1500 0,3000");
  await sleep(900);
  const toastN = await eval_(`document.querySelectorAll("#toastRegion .toast").length`);
  const bAfter = await eval_(
    `api("boundary 20").then(r=>JSON.stringify(r.loops))`);
  console.log("toast:", toastN, toastN > 0 ? "✓" : "✗",
    "| boundary 未變:", bSnap === bAfter ? "✓" : "✗");

  console.log("=== P3-6. Esc 回世界；游離面放置表單 ===");
  /* P3-3 把工具停在 hole;Esc 先退出工具層級,先歸零再按 Esc 才會離開工作區 */
  await eval_(`document.querySelector('[data-face-tool="select"]').click()`);
  await sleep(200);
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(500);
  console.log("focus:", await eval_(`JSON.stringify(oc.focus)`));
  /* 建游離矩形面（DSL + canvas-pos，跟 btnNewRect 同路） */
  const ids6 = await eval_(`api("newid").then(r=>r.boundary)`);
  await cmdLine(`boundary ${ids6} outline 0,0 500,0 500,400 0,400`);
  await eval_(`api("line canvas-pos boundary ${ids6} 700 300")`);
  await eval_(`renderObjects()`);
  await sleep(900);
  const freeCard = await eval_(`(()=>{
    const c = document.querySelector('.ocard[data-id="${ids6}"]');
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  if (freeCard) {
    await dblclick(freeCard.x, freeCard.y);
    await sleep(900);
    const gDis = await eval_(
      `document.querySelector('[data-face-tool="guide"]').disabled`);
    console.log("guide 工具 disabled（游離）:", gDis ? "✓" : "✗");
    /* 工作區檢視器放置表單：天花預設 + origin 0 0 2500 */
    await eval_(`document.querySelector('#faceInspectorContent [data-place-preset="天花"]').click()`);
    await eval_(`(()=>{const p=document.getElementById("faceInspectorContent");
      p.querySelector("#placeOX").value=0; p.querySelector("#placeOY").value=0;
      p.querySelector("#placeOZ").value=2500;})()`);
    await eval_(`document.querySelector("#faceInspectorContent #placeSubmit").click()`);
    await sleep(1200);
    const placed = await eval_(
      `api("objects").then(r=>{const f=r.faces.find(x=>x.id===${ids6});return f&&f.placed})`);
    const surfN = await eval_(
      `api("surfaces").then(r=>r.surfaces.filter(s=>s.boundary===${ids6}).length)`);
    console.log("placed:", placed, placed === true ? "✓" : "✗",
      "| surfaces:", surfN, surfN === 1 ? "✓" : "✗");
    const gEn = await eval_(
      `!document.querySelector('[data-face-tool="guide"]').disabled`);
    console.log("guide 工具啟用（已放置）:", gEn ? "✓" : "✗");
    /* 放置後拉參考線成功 */
    await eval_(`document.querySelector('[data-face-tool="guide"]').click()`);
    await sleep(200);
    const fc2 = await eval_(`(()=>{
      const r = document.getElementById("faceEditorViewport").getBoundingClientRect();
      return {x: r.left + r.width/2, y: r.top + r.height/2};
    })()`);
    await drag(fc2.x - 60, fc2.y, fc2.x + 60, fc2.y + 3);
    await sleep(900);
    const d3 = await eval_(`api("dump").then(r=>r.text)`);
    const valid = (await eval_(`api("references")`)).guides.every(g => !/^-?\d+$/.test(g.expression));
    console.log("放置後參考線皆保留引用式:", valid ? "✓" : "✗");
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    await sleep(400);
  } else console.log("✗ 游離面卡未出現");

  /* ================= Phase 4：空間工作區 ================= */
  /* WORLD_MAX_BOUNDARIES=8：清掉前面累積的面再測六面盒;
     P3-6 結尾焦點可能還在面工作區,先明確退出 */
  await eval_(`leaveFocus()`);
  await eval_(`api("line reset")`);
  await eval_(`renderObjects()`);
  await sleep(600);
  console.log("=== P4-1. 快速六面盒 4000/3000/2500 ===");
  const objPre = await eval_(
    `api("objects").then(r=>({f:r.faces.length,s:r.spaces.length}))`);
  await eval_(`document.getElementById("btnBox6").click()`);
  await sleep(300);
  console.log("box6 dialog:", await eval_(
    `!document.getElementById("box6Dialog").hidden ? "✓ 開啟" : "✗"`));
  await eval_(`document.getElementById("box6Submit").click()`);
  await sleep(1500);
  const objBox = await eval_(
    `api("objects").then(r=>({f:r.faces.length,s:r.spaces.length,
      closed:r.spaces.map(x=>[x.id,x.closed,x.members.length])}))`);
  const boxSp = objBox.closed.find(x => x[2] === 6);
  console.log("objects:", JSON.stringify(objPre), "->", JSON.stringify(objBox));
  console.log("六面盒:", objBox.f === objPre.f + 6 && objBox.s === objPre.s + 1 &&
    boxSp && boxSp[1] === true ? `✓ 6面+1空間 closed:true (空間 ${boxSp && boxSp[0]})` : "✗");
  const boxSid = boxSp && boxSp[0];

  console.log("=== P4-2. 空間工作區：成員/槽位/三視圖 ===");
  const spCard = await eval_(`(()=>{
    const c = document.querySelector('.ocard[data-kind="space"][data-id="${boxSid}"]');
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  if (spCard) {
    await dblclick(spCard.x, spCard.y);
    await sleep(1100);
    console.log("focus:", await eval_(`JSON.stringify(oc.focus)`),
      await eval_(`oc.focus && oc.focus.t==="space" ? "✓" : "✗"`));
    console.log("space layout:", await eval_(
      `!document.getElementById("spaceWorkspaceLayout").hidden ? "✓" : "✗"`));
    const memN = await eval_(
      `document.querySelectorAll("#spaceMemberList .space-boundary-button").length`);
    const slotOn = await eval_(
      `document.querySelectorAll("#spaceInspectorContent .slot.on").length`);
    const projKids = await eval_(
      `document.getElementById("spaceProjSvg").childElementCount`);
    console.log("成員列:", memN, memN === 6 ? "✓" : "✗",
      "| 槽位佔用:", slotOn, slotOn === 6 ? "✓" : "✗",
      "| 三視圖群組:", projKids, projKids >= 3 ? "✓" : "✗");
  } else console.log("✗ 六面盒空間卡未出現");

  console.log("=== P4-3. 編輯成員：移除一面 → closed:false ===");
  await eval_(`document.getElementById("spEditMembers").click()`);
  await sleep(400);
  console.log("member dialog:", await eval_(
    `!document.getElementById("memberDialog").hidden ? "✓" : "✗"`));
  /* 取消勾選第一個成員 */
  await eval_(`(()=>{
    const c = document.querySelector('#memberCheckList input:checked');
    if (c) c.checked = false;
  })()`);
  await eval_(`document.getElementById("memberSubmit").click()`);
  await sleep(1200);
  const spAfterEdit = await eval_(
    `api("objects").then(r=>r.spaces.find(s=>s.id===${boxSid}))`);
  console.log("members:", spAfterEdit && spAfterEdit.members.length,
    spAfterEdit && spAfterEdit.members.length === 5 ? "✓" : "✗",
    "| closed:", spAfterEdit && spAfterEdit.closed,
    spAfterEdit && spAfterEdit.closed === false ? "✓ closed:false" : "✗");

  console.log("=== P4-4. Esc 回世界；mutate 第4行送錯回滾 ===");
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(400);
  console.log("focus:", await eval_(`JSON.stringify(oc.focus)`));
  const objPre2 = await eval_(
    `api("objects").then(r=>({f:r.faces.length,s:r.spaces.length}))`);
  const ids9 = await eval_(`api("newid").then(r=>r.boundary)`);
  /* 世界已有 6/8 邊界:2 面 + 空間重宣告(收成 1 成員,真的改變狀態) + 第4行錯 + 1 */
  const boxMem1 = await eval_(
    `api("objects").then(r=>r.spaces.find(s=>s.id===${boxSid}).members[0])`);
  const mutR = await eval_(`mutate([
    "boundary ${ids9} outline 0,0 100,0 100,100 0,100",
    "boundary ${ids9 + 1} outline 0,0 100,0 100,100 0,100",
    "space ${boxSid} boundary ${boxMem1}",
    "bogus_command_xyz",
    "boundary ${ids9 + 2} outline 0,0 100,0 100,100 0,100"
  ])`);
  await sleep(900);
  const objPost = await eval_(
    `api("objects").then(r=>({f:r.faces.length,s:r.spaces.length,
      mem:r.spaces.find(s=>s.id===${boxSid}).members.length}))`);
  console.log("mutate 回傳:", mutR,
    "| objects:", JSON.stringify(objPre2), "->", JSON.stringify(objPost),
    objPost.f === objPre2.f && objPost.s === objPre2.s && objPost.mem === 5
      ? "✓ 已回滾(含空間成員還原)" : "✗");


  console.log("=== P5. 鍵盤表(主畫布 v/h/f/1、/ 搜尋)===");
  const kbR = await eval_(`(async()=>{
    const press = k => window.dispatchEvent(new KeyboardEvent("keydown",{key:k,bubbles:true}));
    const rel   = k => window.dispatchEvent(new KeyboardEvent("keyup",{key:k,bubbles:true}));
    press("h"); const t1 = oc.tool;
    press("v"); const t2 = oc.tool;
    oc.zoom = 0.5; ocApply(); press("1"); const z1 = oc.zoom;
    press("f"); await new Promise(r=>setTimeout(r,50));
    press(" "); const sp = !!oc.spacePan; rel(" ");
    press("/"); const foc = document.activeElement === searchInput;
    searchInput.blur();
    return {t1,t2,z1,sp,foc};
  })()`);
  console.log("h→", kbR.t1, "| v→", kbR.t2, "| 1→zoom", kbR.z1,
    "| space→", kbR.sp, "| / →搜尋", kbR.foc,
    kbR.t1==="pan" && kbR.t2==="select" && kbR.z1===1 && kbR.sp===true && kbR.foc===true ? "✓" : "✗");

  /* 投影面板互動(§5.5.4):建 guide 後 hover → pick 命中 + overlay 有線 */
  console.log("=== P5b. 空間工作區投影 hover/pick ===");
  const projR = await eval_(`(async()=>{
    leaveFocus();
    if (!oc.spaces.length) return {err:"no space"};
    /* 在一個已放置成員面上建 guide v=2000(預設視圖可見) */
    const sid = oc.surfs[0] && oc.surfs[0].id;
    const gid = (await api("newid")).guide;
    await api("line spec 投影線 2000");
    await api("line guide " + gid + " " + sid + " v spec:投影線");
    await enterFocus("space", oc.spaces[0].id);
    const svg = document.querySelector("#spaceProjSvg");
    if (!svg) return {err:"no svg"};
    /* 在三視圖各自的局部範圍內掃點,找 guide>=0 的命中座標 */
    const views = (await api("render")).layout.views;
    let hit = null;
    outer:
    for (let v = 0; v < 3; ++v) {
      const L = views[v], b = L.bounds;
      for (let y = b[1]; y <= b[3]; y += 250)
        for (let x = b[0]; x <= b[2]; x += 250) {
          const p = await api("pick " + v + " " + x + " " + y + " 20");
          if (p.guide >= 0) { hit = {v, x, y}; break outer; }
        }
    }
    if (!hit) return {err:"guide 在三視圖都掃不到"};
    const L = views[hit.v];
    const pt = svg.createSVGPoint();
    pt.x = hit.x + L.tx; pt.y = hit.y + L.ty;
    const sc = pt.matrixTransform(svg.getScreenCTM());
    svg.dispatchEvent(new PointerEvent("pointermove",
      {clientX: sc.x, clientY: sc.y, bubbles: true}));
    await new Promise(r=>setTimeout(r,600));
    const ov = svg.querySelector("g:last-child").childElementCount;
    const hov = document.getElementById("hovertxt").textContent;
    return {hit, ov, hov};
  })()`);
  console.log("proj hover:", JSON.stringify(projR),
    projR.ov > 0 ? "✓ pick/hover 有回應" : "✗");
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* Q1:delete 指令——拒絕路徑 + UI 刪除鈕交易 + guide 刪除 */
  console.log("=== P6. delete(Q1)===");
  const delR = await eval_(`(async()=>{
    await api("line reset");
    /* C4:deleteObject 已不呼叫 confirm()——不再需要 stub。 */
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 100,0 100,100 0,100");
    const refuse = await api("line delete boundary 1");
    await deleteObject("boundary", 1);           /* 檢視器路徑:先 placement 再 boundary */
    const after1 = (await api("objects")).faces.length;
    /* guide:面內圖層列 ✕ 路徑 = emitLine("delete guide id") */
    await api("line surface 2 origin 0 0 0 u +x v +y outline 0,0 200,0 200,100 0,100");
    const gid = (await api("newid")).guide;
    await emitLine("guide " + gid + " 2 v 50");
    await emitLine("delete guide " + gid);
    const noGuide = !(await api("dump")).text.includes("guide " + gid);
    /* space */
    await api("line space 9");
    await deleteObject("space", 9);
    const spLeft = (await api("objects")).spaces.length;
    return {refuse: refuse.ok, msg: refuse.error,
            after1, noGuide, spLeft};
  })()`);
  console.log("boundary 拒絕:", !delR.refuse ? "✓" : "✗", delR.msg || "",
    "| 刪除後面數:", delR.after1, delR.after1 === 0 ? "✓" : "✗",
    "| guide 已刪:", delR.noGuide ? "✓" : "✗",
    "| 空間已刪:", delR.spLeft === 0 ? "✓" : "✗");

  /* Q2:插入凹口——邊上點一下,頂點 4→8 且核心仍判合法 */
  console.log("=== P7. 插入凹口(Q2)===");
  const insR = await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 200,0 200,100 0,100");
    await renderObjects();
    await enterFocus("face", 1);
    feSetTool("insert");
    const hit = document.querySelector('[data-face-hit="e:0:0"]');
    const b0v = (await api("boundary 1")).loops[0].verts;
    const mid = [(b0v[0][0]+b0v[1][0])/2, (b0v[0][1]+b0v[1][1])/2];
    await feDown({x: mid[0], y: mid[1]}, {target: hit, clientX: 0, clientY: 0});
    /* Phase 2:點邊開 #notchDialog,確認才插入 */
    const dlg = !$("notchDialog").hidden;
    $("notchSubmit").click();
    await new Promise(r=>setTimeout(r,300));
    const b = await api("boundary 1");
    const ortho = b.ok && b.loops[0].verts.every((v,i,vs)=>{
      const nx = vs[(i+1)%vs.length];
      return v[0]===nx[0] || v[1]===nx[1];
    });
    return {tool: fe.tool, verts: b.loops[0].verts.length,
            fixity: b.loops[0].fixity.length, ortho, dlg};
  })()`);
  console.log("insert 工具:", insR.tool === "insert" ? "✓" : "✗",
    "| 對話框:", insR.dlg ? "✓" : "✗",
    "| 頂點 4→", insR.verts, insR.verts === 8 ? "✓" : "✗",
    "| fixity 同步:", insR.fixity === 8 ? "✓" : "✗",
    "| 全正交:", insR.ortho ? "✓" : "✗");
  /* 拖凹口底部頂點加深 → 仍合法(用既有頂點拖曳路徑) */
  const notchR = await eval_(`(async()=>{
    feSetTool("select");
    fe.work = (await api("boundary 1")).loops.map(l=>({verts:l.verts.map(p=>[...p]),fixity:[...l.fixity]}));
    fe.work[0].verts[2][1] += 30;   /* 凹底左點再往下 30 */
    fe.work[0].verts[3][1] += 30;   /* 凹底右點同步 */
    const ok = await emitBoundary(1, fe.work);
    fe.work = null;
    const b1 = await api("boundary 1");
    return {ok, verts: b1.loops[0].verts.length};
  })()`);
  console.log("凹口加深:", notchR.ok ? "✓" : "✗",
    "| 頂點:", notchR.verts, notchR.verts === 8 ? "✓" : "✗");
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* Q3:角材/網格圖形化——工具點放角材、表單建網格、圖層列刪除 */
  console.log("=== P8. 角材與網格(Q3)===");
  const q3R = await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    await renderObjects();
    await enterFocus("face", 1);
    /* 角材:設定 L/A/B + 方向 + 深度 → timber 工具點 (500,300) */
    $("tbAnchor").value = "at-face e0"; $("tbRole").value = "boundary"; $("tbA").value = "27"; $("tbB").value = "33";
    $("tbDir").value = "+u"; $("tbSide").value = "+n";
    feSetTool("timber");
    await feDown({x: 500, y: 300}, {target: $("faceEditorSvg"), clientX: 0, clientY: 0});
    await new Promise(r=>setTimeout(r,300));
    const dump1 = (await api("dump")).text;
    const hasTimber = /timber \\d+ 27 33 role boundary/.test(dump1) &&
                      /place \\d+ on \\d+ at-face e0 \\+u \\+n/.test(dump1);
    const fp = document.querySelector(".face-timber");
    /* 網格:表單建 u 500 1500 / v 300 900 */
    $("gridU").value = "500 1500"; $("gridV").value = "300 900";
    $("gridCreate").click();
    await new Promise(r=>setTimeout(r,300));
    const dump2 = (await api("dump")).text;
    const hasGrid = /grid \\d+ on \\d+ u 500 1500/.test(dump2) &&
                    /grid \\d+ on \\d+ v 300 900/.test(dump2);
    const gridLines = document.querySelectorAll(".face-grid-line").length;
    const rows = [...document.querySelectorAll(".face-layer-row strong")]
      .map(x => x.textContent).join("|");
    return {hasTimber, fp: !!fp, hasGrid, gridLines, rows};
  })()`);
  console.log("角材放置:", q3R.hasTimber ? "✓" : "✗",
    "| 足跡繪製:", q3R.fp ? "✓" : "✗",
    "| 網格建立:", q3R.hasGrid ? "✓" : "✗",
    "| 網格線數:", q3R.gridLines, q3R.gridLines === 4 ? "✓" : "✗",
    "| 圖層列:", /角材/.test(q3R.rows) && /網格/.test(q3R.rows) ? "✓" : "✗");
  /* 足跡越界 → 核心拒絕,toast + dump 不變 */
  const q3b = await eval_(`(async()=>{
    const before = (await api("dump")).text;
    feSetTool("timber");
    await feDown({x: 3999, y: 2999}, {target: $("faceEditorSvg"), clientX: 0, clientY: 0});
    await new Promise(r=>setTimeout(r,300));
    const after = (await api("dump")).text;
    const toastShown = [...document.querySelectorAll(".toast")]
      .map(t => t.textContent).join("|");
    return {same: before === after, toast: toastShown};
  })()`);
  console.log("越界拒絕:", q3b.same ? "✓" : "✗",
    "| toast:", q3b.toast ? "✓" : "✗");
  /* 圖層列 ✕ 刪角材與網格 */
  const q3c = await eval_(`(async()=>{
    const dels = [...document.querySelectorAll(".face-layer-del")];
    for (const b of dels) { b.click(); await new Promise(r=>setTimeout(r,200));
      const confirm=document.querySelector("#impact-confirm"); if (confirm && !confirm.disabled) { confirm.click(); await new Promise(r=>setTimeout(r,200)); } }
    const dump = (await api("dump")).text;
    return {noTimber: !/timber /.test(dump), noGrid: !/grid /.test(dump)};
  })()`);
  console.log("角材已刪:", q3c.noTimber ? "✓" : "✗",
    "| 網格已刪:", q3c.noGrid ? "✓" : "✗");
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* RC/多邊形 Phase 1:重畫外環 + 形狀庫 */
  console.log("=== P9. 重畫外環與形狀庫(RC Phase 1)===");
  const rw = await eval_(`(async()=>{
    await api("line reset");
    await api("line boundary 1 outline 0,0 400,0 400,300 0,300");
    await renderObjects();
    await enterFocus("face", 1);
    /* L 形:6 點軸鎖,Enter 閉合 */
    feSetTool("redraw");
    const pts = [[50,50],[350,50],[350,150],[150,150],[150,280],[50,280]];
    for (const p of pts)
      await feDown({x:p[0],y:p[1]}, {target:$("faceEditorSvg"),clientX:0,clientY:0});
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter"}));
    await new Promise(r=>setTimeout(r,300));
    const b = await api("boundary 1");
    const ortho = b.loops[0].verts.every((v,i,vs)=>{
      const nx = vs[(i+1)%vs.length];
      return v[0]===nx[0] || v[1]===nx[1];
    });
    return {tool:"redraw", verts:b.loops[0].verts.length, ortho,
            fixity:b.loops[0].fixity.length};
  })()`);
  console.log("L 形閉合:", rw.verts === 6 ? "✓" : "✗",
    "| 頂點:", rw.verts, "| 全正交:", rw.ortho ? "✓" : "✗",
    "| fixity:", rw.fixity === 6 ? "✓" : "✗");
  /* Esc 取消:畫一半按 Esc → boundary 不變 */
  const rw2 = await eval_(`(async()=>{
    feSetTool("redraw");
    await feDown({x:10,y:10},{target:$("faceEditorSvg"),clientX:0,clientY:0});
    await feDown({x:90,y:10},{target:$("faceEditorSvg"),clientX:0,clientY:0});
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"}));
    const b = await api("boundary 1");
    return {verts:b.loops[0].verts.length, draft:!!fe.drag};
  })()`);
  console.log("Esc 取消:", rw2.verts === 6 && !rw2.draft ? "✓" : "✗",
    "| 草稿已清:", !rw2.draft ? "✓" : "✗");
  /* 共線點自動去除:4 點中夾一個共線 → 仍 4 頂點 */
  const rw3 = await eval_(`(async()=>{
    feSetTool("redraw");
    const pts = [[0,0],[200,0],[300,0],[300,200],[0,200]];   /* 200,0 與 300,0 共線 */
    for (const p of pts)
      await feDown({x:p[0],y:p[1]},{target:$("faceEditorSvg"),clientX:0,clientY:0});
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter"}));
    await new Promise(r=>setTimeout(r,300));
    const b = await api("boundary 1");
    return {verts:b.loops[0].verts.length};
  })()`);
  console.log("共線去除:", rw3.verts === 4 ? "✓" : "✗", "| 頂點:", rw3.verts);
  /* 形狀庫:L 4000/3000/臂1000 → 6 頂點、面積 = 4000*3000-3000*2000 */
  const rw4 = await eval_(`(async()=>{
    feSetTool("select");
    $("faceShapeButton").click();
    $("shapeW").value="4000"; $("shapeD").value="3000"; $("shapeA").value="1000";
    $("shapeSubmit").click();
    await new Promise(r=>setTimeout(r,300));
    const b = await api("boundary 1");
    const vs = b.loops[0].verts;
    let area = 0;
    for (let i=0;i<vs.length;++i){
      const p=vs[i], q=vs[(i+1)%vs.length];
      area += p[0]*q[1]-q[0]*p[1];
    }
    return {verts:vs.length, area:Math.abs(area)/2,
            dlg:$("shapeDialog").hidden};
  })()`);
  console.log("形狀庫 L:", rw4.verts === 6 ? "✓" : "✗",
    "| 面積:", rw4.area, rw4.area === 6000000 ? "✓" : "✗",
    "| 對話框已關:", rw4.dlg ? "✓" : "✗");
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* RC/多邊形 Phase 2:尺寸導向編輯 */
  console.log("=== P10. 尺寸導向編輯(RC Phase 2)===");
  /* 鍵入長度:redraw 中數字鍵 + Enter → 下一段長度即所鍵 */
  const tl = await eval_(`(async()=>{
    await api("line reset");
    await api("line boundary 1 outline 0,0 400,0 400,300 0,300");
    await renderObjects();
    await enterFocus("face", 1);
    feSetTool("redraw");
    await feDown({x:0,y:0},{target:$("faceEditorSvg"),clientX:0,clientY:0});
    await feMove({x:500,y:3});              /* 游標朝 +u → 軸向 +u */
    for (const ch of ["1","2","0","0"])
      window.dispatchEvent(new KeyboardEvent("keydown",{key:ch}));
    const bufShown = !$("feLenInput").hidden && $("feLenInput").value === "1200";
    /* Esc 只清輸入不取消整段 */
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"}));
    const draftKept = !!fe.drag && fe.lenBuf === "" && $("feLenInput").hidden;
    for (const ch of ["1","5","0","0"])
      window.dispatchEvent(new KeyboardEvent("keydown",{key:ch}));
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter"}));
    const last = fe.drag.pts[fe.drag.pts.length - 1];
    return {bufShown, draftKept, last};
  })()`);
  console.log("鍵入長度:", tl.last[0] === 1500 && tl.last[1] === 0 ? "✓" : "✗",
    "| 浮動框:", tl.bufShown ? "✓" : "✗",
    "| Esc 只清輸入:", tl.draftKept ? "✓" : "✗");
  /* 邊長清單:edge0 400→500,右半邊整串 +100x(矩形 500×300) */
  const el1 = await eval_(`(async()=>{
    window.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"}));  /* 丟草稿 */
    feSetTool("select");
    const inp = document.querySelector('[data-edge-len="0"]');
    inp.value = "500";
    inp.dispatchEvent(new Event("change"));
    await new Promise(r=>setTimeout(r,300));
    const b = await api("boundary 1");
    const vs = b.loops[0].verts;
    const w = vs[1][0] - vs[0][0], h = vs[2][1] - vs[1][1];
    return {w, h, verts: vs.length};
  })()`);
  console.log("邊長清單:", el1.w === 500 && el1.h === 300 ? "✓" : "✗",
    "| 結果:", el1.w + "×" + el1.h, "| 頂點:", el1.verts);
  /* 單擊邊切 fixity:select 點邊不動 → F→X */
  const fx = await eval_(`(async()=>{
    feSetTool("select");
    const hit = document.querySelector('[data-face-hit="e:0:0"]');
    const before = (await api("boundary 1")).loops[0].fixity[0];
    await feDown({x:250,y:0},{target:hit,clientX:0,clientY:0});
    await feUp({x:250,y:0},{target:hit,clientX:0,clientY:0});
    await new Promise(r=>setTimeout(r,300));
    const after = (await api("boundary 1")).loops[0].fixity[0];
    return {before, after};
  })()`);
  console.log("點邊切 fixity:", fx.before === 1 && fx.after === 0 ? "✓" : "✗",
    "|", fx.before, "→", fx.after);
  /* 參數化凹口:insert 點邊 → 對話框,w=40 d=20 → 4→8 頂點 */
  const nt = await eval_(`(async()=>{
    feSetTool("insert");
    const hit = document.querySelector('[data-face-hit="e:0:0"]');
    await feDown({x:250,y:0},{target:hit,clientX:0,clientY:0});
    const dlgOpen = !$("notchDialog").hidden;
    $("notchW").value = "40"; $("notchD").value = "20";
    $("notchSubmit").click();
    await new Promise(r=>setTimeout(r,300));
    const b = await api("boundary 1");
    const vs = b.loops[0].verts;
    /* 凹口深 20:找 y=20 的頂點(內側朝下) */
    const depth = vs.filter(p => p[1] === 20).length;
    return {dlgOpen, closed: $("notchDialog").hidden,
            verts: vs.length, depth};
  })()`);
  console.log("參數化凹口:", nt.dlgOpen && nt.closed ? "✓" : "✗",
    "| 頂點 4→", nt.verts, nt.verts === 8 ? "✓" : "✗",
    "| 凹深 20:", nt.depth === 2 ? "✓" : "✗");
  /* 拖邊對齊吸附:L 形拖邊經過他頂點同軸座標 → snapTo */
  const sn = await eval_(`(async()=>{
    await api("line reset");
    await api("line boundary 1 outline 0,0 300,0 300,100 100,100 100,300 0,300");
    oc.focus = null; oc.stack = [];         /* 前段已在面 1,勿再推疊 */
    await renderObjects();
    await enterFocus("face", 1);
    feSetTool("select");
    const hit = document.querySelector('[data-face-hit="e:0:0"]');
    await feDown({x:150,y:0},{target:hit,clientX:0,clientY:0});
    await feMove({x:150,y:103});            /* 接近 v=100 的頂點軸 */
    const snap = fe.drag.snapTo;
    const movedY = fe.work[0].verts[0][1];
    fe.work = null; fe.drag = null;         /* 不落地,只驗吸附偵測 */
    return {snap, movedY};
  })()`);
  console.log("對齊吸附:", sn.snap === 100 ? "✓" : "✗",
    "| snapTo:", sn.snap, "| 吸附後 v:", sn.movedY);
  await eval_(`leaveFocus()`);
  await sleep(300);

  console.log("=== P11. RC 柱樑一等物件(RC Phase 4)===");
  await eval_(`(async()=>{
    await api("line reset");
    for (const ln of [
      "boundary 1 outline 0,0 4000,0 4000,3000 0,3000",
      "placement 1 on boundary 1 origin 0 0 2500 u +x v +y",
      "boundary 2 outline 0,0 3000,0 3000,4000 0,4000",
      "placement 2 on boundary 2 origin 0 0 0 u +y v +x",
      "space 1 boundary 1 2",
    ]) await api("line " + ln);
    await renderObjects();
  })()`);
  await sleep(700);
  /* ＋柱:對話框 → 選空間 → 建立 */
  await eval_(`document.getElementById("btnNewColumn").click()`);
  await sleep(300);
  console.log("rcDialog:", await eval_(
    `!document.getElementById("rcDialog").hidden ? "✓ 開啟" : "✗"`));
  await eval_(`(()=>{
    document.getElementById("rcSpace").value = "1";
    document.getElementById("rcX").value = "500";
    document.getElementById("rcY").value = "500";
  })()`);
  await eval_(`document.getElementById("rcSubmit").click()`);
  await sleep(1000);
  const colObj = await eval_(`api("objects").then(r=>r.columns)`);
  console.log("柱建立:", colObj.length === 1 && colObj[0].space === 1
    ? `✓ id=${colObj[0].id} z=${colObj[0].box[2]}~${colObj[0].box[5]}`
    : "✗ " + JSON.stringify(colObj));
  const colCard = await eval_(`(()=>{
    const c = document.querySelector('.ocard[data-kind="column"]');
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  console.log("柱卡片:", colCard ? "✓" : "✗");
  /* 拖卡片 → canvas-pos 持久化 */
  if (colCard) {
    await drag(colCard.x, colCard.y, colCard.x + 130, colCard.y + 80);
    await sleep(800);
    const dragR = await eval_(`api("objects").then(r=>({
      has: r.columns[0] && r.columns[0].hasPos }))`);
    const dumpPos = await eval_(
      `api("dump").then(d=>/canvas-pos column/.test(d.text))`);
    console.log("拖卡片→canvas-pos:", dragR.has && dumpPos ? "✓" : "✗",
      "| dump 有記錄:", dumpPos);
  }
  /* 空間→柱 障礙連線 */
  const rcEdgeLabels = await eval_(
    `[...document.querySelectorAll("#edgeLabelLayer .edge-label")].map(t=>t.textContent).join(",")`);
  console.log("障礙連線:", /障礙/.test(rcEdgeLabels) ? `✓ ${rcEdgeLabels}` : `✗ ${rcEdgeLabels}`);
  /* ＋樑 */
  await eval_(`document.getElementById("btnNewBeam").click()`);
  await sleep(300);
  await eval_(`(()=>{
    document.getElementById("rcSpace").value = "1";
    document.getElementById("rcA").value = "0";
    document.getElementById("rcB").value = "4000";
    document.getElementById("rcC").value = "1500";
  })()`);
  await eval_(`document.getElementById("rcSubmit").click()`);
  await sleep(1000);
  const beamObj = await eval_(`api("objects").then(r=>r.beams)`);
  console.log("樑建立:", beamObj.length === 1 && beamObj[0].box[5] === 2500
    ? `✓ top=${beamObj[0].box[5]}` : "✗ " + JSON.stringify(beamObj));
  console.log("樑卡片:", await eval_(
    `!!document.querySelector('.ocard[data-kind="beam"]') ? "✓" : "✗"`));
  /* 搜尋「柱」命中柱卡 */
  await eval_(`(()=>{ const s=document.getElementById("searchInput");
    s.value="柱"; s.dispatchEvent(new Event("input")); })()`);
  await sleep(400);
  const srch = await eval_(`(()=>{
    const cards=[...document.querySelectorAll("#cardLayer .ocard")];
    return {n:cards.length, kind:cards[0] && cards[0].dataset.kind};
  })()`);
  console.log("搜尋柱:", srch.n === 1 && srch.kind === "column" ? "✓" : `✗ ${JSON.stringify(srch)}`);
  await eval_(`(()=>{ const s=document.getElementById("searchInput");
    s.value=""; s.dispatchEvent(new Event("input")); })()`);
  await sleep(400);
  /* 檢視器表單 → 重宣告 */
  await eval_(`selectObject("column", ${colObj[0].id})`);
  await sleep(500);
  console.log("檢視器表單:", await eval_(
    `!!document.getElementById("rcfX") ? "✓" : "✗"`));
  await eval_(`document.getElementById("rcfX").value = "800"`);
  await eval_(`document.getElementById("rcfApply").click()`);
  await sleep(900);
  const movedX = await eval_(`api("objects").then(r=>r.columns[0].box[0])`);
  console.log("表單重宣告 x→800:", movedX === 800 ? "✓" : `✗ ${movedX}`);
  /* 雙擊柱卡 → 只開只開檢視器(🔒 Q10) */
  const cc = await eval_(`(()=>{
    const c = document.querySelector('.ocard[data-kind="column"]');
    const r = c.getBoundingClientRect();
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  })()`);
  await dblclick(cc.x, cc.y);
  await sleep(700);
  const dbl = await eval_(`({f:oc.focus, s:oc.sel && oc.sel.kind})`);
  console.log("雙擊只開檢視器:", dbl.f === null && dbl.s === "column" ? "✓" : `✗ ${JSON.stringify(dbl)}`);
  /* 刪除 → 卡片消失(C4:deleteObject 已不呼叫 confirm(),不再需要 stub） */
  await eval_(`document.getElementById("inspDelete").click()`);
  await sleep(900);
  const gone = await eval_(`api("objects").then(r=>r.columns.length === 0)`);
  const cardGone = await eval_(`!document.querySelector('.ocard[data-kind="column"]')`);
  console.log("刪除→卡片消失:", gone && cardGone ? "✓" : `✗ obj=${gone} card=${cardGone}`);

  console.log("=== P12. 空間工作區:平面示意+構件+鬼影(RC Phase 5)===");
  /* 等前段 mutate 完全沉降,避免 emitLine 撞 oc.busy */
  await eval_(`new Promise(r=>{const t=()=>oc.busy?setTimeout(t,60):r();t()})`);
  await eval_(`(async()=>{
    await api("line reset");
    for (const ln of [
      "boundary 1 outline 0,0 4000,0 4000,3000 0,3000",
      "placement 1 on boundary 1 origin 0 0 2500 u +x v +y",
      "boundary 2 outline 0,0 3000,0 3000,4000 0,4000",
      "placement 2 on boundary 2 origin 0 0 0 u +y v +x",
      "boundary 3 outline 0,0 4000,0 4000,2500 0,2500",
      "placement 3 on boundary 3 origin 0 0 0 u +x v +z",
      "boundary 4 outline 0,0 2500,0 2500,4000 0,4000",
      "placement 4 on boundary 4 origin 0 3000 0 u +z v +x",
      "boundary 5 outline 0,0 2500,0 2500,3000 0,3000",
      "placement 5 on boundary 5 origin 0 0 0 u +z v +y",
      "boundary 6 outline 0,0 3000,0 3000,2500 0,2500",
      "placement 6 on boundary 6 origin 4000 0 0 u +y v +z",
      "space 1 boundary 1 2 3 4 5 6",
      "column 1 in 1 at 1000 1000 size 400 400",
      "beam 1 in 1 along y from 0 to 3000 at 2000 width 300 depth 500",
    ]) await api("line " + ln);
    await renderObjects();
    await enterFocus("space", 1);
  })()`);
  await sleep(1000);
  const plan0 = await eval_(`({
    cols: document.querySelectorAll("#spacePlanSvg .space-plan-col").length,
    beams: document.querySelectorAll("#spacePlanSvg .space-plan-beam").length,
    mine: document.querySelectorAll("#spaceRcList .space-boundary-button").length,
    free: document.querySelectorAll("#spaceRcFreeList .space-boundary-button").length,
    floor: !!document.querySelector("#spacePlanSvg .space-plan-floor")
  })`);
  console.log("平面圖:", plan0.floor && plan0.cols === 1 && plan0.beams === 1
    ? "✓" : `✗ ${JSON.stringify(plan0)}`);
  console.log("構件清單:", plan0.mine === 2 && plan0.free === 0
    ? "✓" : `✗ ${JSON.stringify(plan0)}`);

  /* 點放柱:房間 (1500,500) → at 1200 200 size 600;
     房間→螢幕走 CTM(preserveAspectRatio letterbox 也算進去) */
  const ptCol = await eval_(`(()=>{
    const svg = document.getElementById("spacePlanSvg");
    const pt = svg.createSVGPoint(); pt.x = 1500; pt.y = 500;
    const p = pt.matrixTransform(svg.getScreenCTM());
    return {x: p.x, y: p.y};
  })()`);
  await click(ptCol.x, ptCol.y);
  await sleep(1000);
  const colP = await eval_(`api("objects").then(r=>({
    n: r.columns.length,
    dom: document.querySelectorAll("#spacePlanSvg .space-plan-col").length
  }))`);
  console.log("點放柱:", colP.n === 2 && colP.dom === 2
    ? "✓" : `✗ ${JSON.stringify(colP)}`);

  /* 拖放樑:水平拖 → along x;房間→螢幕走 CTM */
  const bmD = await eval_(`(()=>{
    const svg = document.getElementById("spacePlanSvg");
    const px = (x,y)=>{ const pt = svg.createSVGPoint(); pt.x = x; pt.y = y;
      const p = pt.matrixTransform(svg.getScreenCTM()); return {x: p.x, y: p.y}; };
    return {a: px(300, 2400), b: px(2700, 2450)};
  })()`);
  await drag(bmD.a.x, bmD.a.y, bmD.b.x, bmD.b.y);
  await sleep(1000);
  const beamP = await eval_(`api("objects").then(r=>({
    n: r.beams.length,
    ax: r.beams[1] && r.beams[1].axis,
    dom: document.querySelectorAll("#spacePlanSvg .space-plan-beam").length
  }))`);
  console.log("拖放樑:", beamP.n === 2 && beamP.ax === "x" && beamP.dom === 2
    ? "✓" : `✗ ${JSON.stringify(beamP)}`);

  /* 構件移出→游離列→收進 */
  await eval_(`document.querySelector("#spaceRcList .space-boundary-button").click()`);
  await sleep(900);
  const det = await eval_(`api("objects").then(r=>({
    sp: r.columns[0] && r.columns[0].space,
    free: document.querySelectorAll("#spaceRcFreeList .space-boundary-button").length
  }))`);
  console.log("移出→游離:", det.sp === 0 && det.free === 1
    ? "✓" : `✗ ${JSON.stringify(det)}`);
  await eval_(`document.querySelector("#spaceRcFreeList .space-boundary-button").click()`);
  await sleep(900);
  const att = await eval_(`api("objects").then(r=>r.columns[0] && r.columns[0].space)`);
  console.log("收進→空間:", att === 1 ? "✓" : `✗ ${att}`);

  /* 面內鬼影:天花(面1)應有 柱×2 + 樑條帶×2 = 4 個 */
  await eval_(`leaveFocus()`);
  await sleep(300);
  await eval_(`enterFocus("face", 1)`);
  await sleep(1000);
  const ghost = await eval_(`({
    n: document.querySelectorAll("#faceEditorRoot .obstacle-ghost").length,
    cls: [...document.querySelectorAll("#faceEditorRoot .obstacle-ghost")]
      .map(e=>e.dataset.cls).join(","),
    rows: document.querySelectorAll("#faceLayerList .face-layer-row").length
  })`);
  console.log("面內鬼影:", ghost.n === 4 && ghost.cls.includes("hole")
    && ghost.cls.includes("strip")
    ? "✓" : `✗ ${JSON.stringify(ghost)}`);
  /* 牆面鬼影:y=0 牆(面3)應有 樑1頂凹 + 樑2頂降 */
  await eval_(`leaveFocus()`);
  await sleep(300);
  await eval_(`enterFocus("face", 3)`);
  await sleep(1000);
  const ghostW = await eval_(`[...document.querySelectorAll("#faceEditorRoot .obstacle-ghost")]
    .map(e=>e.dataset.cls).join(",")`);
  console.log("牆面鬼影:", /top_notch/.test(ghostW) ? "✓" : `✗ ${ghostW}`);
  await eval_(`leaveFocus()`);
  await sleep(300);

  console.log("=== P13. apply-proj 套用按鈕(RC Phase 6)===");
  await eval_(`(async()=>{
    await api("line reset");
    for (const ln of [
      "boundary 1 outline 0,0 4000,0 4000,3000 0,3000",
      "placement 1 on boundary 1 origin 0 0 2500 u +x v +y",
      "boundary 2 outline 0,0 3000,0 3000,4000 0,4000",
      "placement 2 on boundary 2 origin 0 0 0 u +y v +x",
      "boundary 3 outline 0,0 4000,0 4000,2500 0,2500",
      "placement 3 on boundary 3 origin 0 0 0 u +x v +z",
      "boundary 4 outline 0,0 2500,0 2500,4000 0,4000",
      "placement 4 on boundary 4 origin 0 3000 0 u +z v +x",
      "boundary 5 outline 0,0 2500,0 2500,3000 0,3000",
      "placement 5 on boundary 5 origin 0 0 0 u +z v +y",
      "boundary 6 outline 0,0 3000,0 3000,2500 0,2500",
      "placement 6 on boundary 6 origin 4000 0 0 u +y v +z",
      "space 1 boundary 1 2 3 4 5 6",
      "column 1 in 1 at 1000 1000 size 400 400",
      "beam 1 in 1 along y from 0 to 3000 at 2000 width 300 depth 500",
    ]) await api("line " + ln);
    await renderObjects();
    await enterFocus("face", 1);
  })()`);
  /* 投影清單是 obstacles 查詢後才渲染:輪詢到 2 個勾選框為止(最多 4.5s),不靠固定 sleep */
  let obUi = null;
  for (let i = 0; i < 15; ++i) {
    await sleep(300);
    obUi = await eval_(`({
      checks: document.querySelectorAll("#faceLayerList .fe-ob-check").length,
      checked: document.querySelectorAll("#faceLayerList .fe-ob-check:checked").length,
      btn: !!document.getElementById("feApplyProj"),
      cut: !!document.getElementById("feCutStrip"),
      btnTxt: document.getElementById("feApplyProj") &&
        document.getElementById("feApplyProj").textContent
    })`);
    if (obUi.checks === 2 && obUi.btn && obUi.cut) break;
  }
  console.log("套用UI:", obUi.checks === 2 && obUi.checked === 1 &&
    obUi.btn && obUi.cut ? "✓" : `✗ ${JSON.stringify(obUi)}`);
  /* 只勾柱(預設)→ 套用 → 孔出現 */
  await eval_(`document.getElementById("feApplyProj").click()`);
  await sleep(1200);
  const ap1 = await eval_(`api("boundary 1").then(b=>({
    loops: b.loops.length, verts: b.loops[0].verts.length,
    holeF: b.loops[1] && b.loops[1].fixity.every(f=>f)
  }))`);
  console.log("套用柱孔:", ap1.loops === 2 && ap1.verts === 4 && ap1.holeF
    ? "✓" : `✗ ${JSON.stringify(ap1)}`);
  /* 只勾樑(取消已套用的柱:重套=拒絕)+ 裁切條帶 → 套用 */
  await eval_(`(()=>{
    for (const c of document.querySelectorAll("#faceLayerList .fe-ob-check")) {
      c.checked = c.dataset.itemType === "beam";
      c.dispatchEvent(new Event("change"));
    }
    const cut=document.getElementById("feCutStrip");
    if(cut) cut.checked=true;
    document.getElementById("feApplyProj").click();
  })()`);
  await sleep(1500);
  const ap2 = await eval_(`api("objects").then(r=>({
    faces: r.faces.length,
    sp: r.spaces[0] && r.spaces[0].members
  }))`);
  console.log("裁切條帶:", ap2.faces === 10 && !ap2.sp.includes(1)
    ? "✓" : `✗ ${JSON.stringify(ap2)}`);
  const apGhost = await eval_(`document.querySelectorAll("#faceEditorRoot .obstacle-ghost").length`);
  console.log("保留片無殘影(柱樑都離開此片):", apGhost === 0 ? "✓" : `✗ ${apGhost}`);
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* ================= P14. 模式回饋 =================
   * 任何工具在任何輸入下都要有可見反應:
   *   切工具 → 狀態列手勢 + 浮標 + 游標類;錯誤手勢 → toast(不靜默);
   *   Esc → 有草稿先清草稿+toast,否則一次離開工作區。 */
  console.log("=== P14. 模式回饋(工具手勢/錯誤輸入/Esc) ===");
  await eval_(`(async()=>{
    await api("line reset");
    for (const ln of [
      "boundary 1 outline 0,0 4000,0 4000,3000 0,3000",
      "placement 1 on boundary 1 origin 0 0 2500 u +x v +y",
    ]) await api("line " + ln);
    await renderObjects();
    await enterFocus("face", 1);
  })()`);
  await sleep(800);
  const fbVp = await eval_(`(()=>{const r=document.getElementById("faceEditorViewport").getBoundingClientRect();
    return {cx: r.left + r.width/2, cy: r.top + r.height/2,
            qx: r.left + r.width*0.3, qy: r.top + r.height*0.32}})()`);
  /* (a) 切工具:狀態列手勢 + 浮標 + 游標類 */
  const fbTool = await eval_(`(()=>{
    document.querySelector('[data-face-tool="guide"]').click();
    return {status: document.getElementById("status").textContent,
            hint: document.getElementById("faceCanvasHint").textContent,
            hintHid: document.getElementById("faceCanvasHint").hidden,
            cls: document.getElementById("faceEditorViewport").className};
  })()`);
  /* B6:浮標只給多步工具(redraw),單發工具看狀態列 */
  console.log("切參考線:狀態列手勢", fbTool.status.includes("拖曳") ? "✓" : "✗ " + fbTool.status,
    "| 浮標隱藏(B6)", fbTool.hintHid ? "✓" : "✗",
    "| 游標類", fbTool.cls.includes("tool-referenceLine") ? "✓" : "✗ " + fbTool.cls);
  /* (b) 參考線只點沒拖 → u/v 小選單 → 選 v → dump 出現 guide */
  await eval_(`(async()=>{const r=document.getElementById("faceEditorViewport").getBoundingClientRect();const p=feSnap(fePoint({clientX:r.left+r.width/2,clientY:r.top+r.height/2}));await api('line spec 點放定位 '+Math.round(p.x))})()`);
  await click(fbVp.cx, fbVp.cy);
  await sleep(400);
  const pkShown = await eval_(`!document.getElementById("feGuidePick").hidden`);
  console.log("參考線點一下→方向選單:", pkShown ? "✓" : "✗");
  const pkBtn = await eval_(`(()=>{const b=document.querySelector('#feGuidePick [data-axis="v"]');
    if(!b) return null; const r=b.getBoundingClientRect();
    return {x:r.left+r.width/2,y:r.top+r.height/2};})()`);
  if (pkBtn) { await click(pkBtn.x, pkBtn.y); await sleep(700); }
  const gDump = await eval_(`api("dump").then(d=>{const m=d.text.match(/^guide (\\d+) (\\d+) v spec:點放定位$/m);return m&&m[0]})`);
  console.log("選 v 後建線:", gDump ? "✓ " + gDump : "✗");
  /* (c) 開口只點沒拖 → toast「拖出矩形」 */
  await eval_(`document.querySelector('[data-face-tool="hole"]').click()`);
  await sleep(250);
  await click(fbVp.qx, fbVp.qy);
  await sleep(350);
  const holeToast = await eval_(
    `[...document.querySelectorAll("#toastRegion .toast")].map(t=>t.textContent).join("|")`);
  console.log("開口只點→toast:", holeToast.includes("拖出矩形") ? "✓" : "✗ " + holeToast);
  /* (d) 凹口點面內 → toast + 邊高亮 */
  await eval_(`document.querySelector('[data-face-tool="insert"]').click()`);
  await sleep(250);
  await click(fbVp.qx, fbVp.qy);
  await sleep(150);
  const insFb = await eval_(`({
    toast:[...document.querySelectorAll("#toastRegion .toast")].map(t=>t.textContent).join("|"),
    flash: document.getElementById("faceEditorViewport").classList.contains("fe-flash-edges")})`);
  console.log("凹口點面內→toast:", insFb.toast.includes("邊上") ? "✓" : "✗ " + insFb.toast,
    "| 邊高亮:", insFb.flash ? "✓" : "✗");
  /* (e) 角材 A 空白 → toast + #tbA 標紅 */
  await eval_(`(()=>{
    document.querySelector('[data-face-tool="timber"]').click();
    const tb=document.getElementById("tbA"); if (tb) tb.value="";
  })()`);
  await sleep(250);
  await click(fbVp.qx, fbVp.qy);
  await sleep(350);
  const tbFb = await eval_(`({
    toast:[...document.querySelectorAll("#toastRegion .toast")].map(t=>t.textContent).join("|"),
    inv: document.getElementById("tbA") && document.getElementById("tbA").classList.contains("invalid")})`);
  console.log("角材A空→toast:", tbFb.toast.includes("截面") ? "✓" : "✗ " + tbFb.toast,
    "| tbA標紅:", tbFb.inv ? "✓" : "✗");
  /* (f) 狀態列綁定工具:切走後上一工具的訊息被手勢取代 */
  const stLife = await eval_(`(()=>{
    document.querySelector('[data-face-tool="select"]').click();
    return document.getElementById("status").textContent;
  })()`);
  console.log("切回選取→狀態列=手勢:", stLife.includes("選取") ? "✓" : "✗ " + stLife);
  /* (g) Esc 一次離開(無草稿,工具非 select 也直接走) */
  await eval_(`document.querySelector('[data-face-tool="insert"]').click()`);
  await sleep(200);
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(400);
  console.log("Esc一次離開:", await eval_(`JSON.stringify(oc.focus)`) === "null" ? "✓" : "✗");
  /* (h) 有草稿 → 第一次 Esc 清草稿+toast,再一次才離開 */
  await eval_(`enterFocus("face", 1)`);
  await sleep(500);
  await eval_(`document.querySelector('[data-face-tool="redraw"]').click()`);
  await sleep(250);
  await click(fbVp.qx, fbVp.qy);
  await click(fbVp.cx, fbVp.cy);
  await sleep(300);
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(300);
  const esc1 = await eval_(`({draft: !!fe.drag, focus: !!oc.focus,
    toast:[...document.querySelectorAll("#toastRegion .toast")].map(t=>t.textContent).join("|")})`);
  console.log("Esc清草稿:", !esc1.draft ? "✓" : "✗",
    "| toast再按Esc:", esc1.toast.includes("再按 Esc") ? "✓" : "✗ " + esc1.toast,
    "| 仍在工作區:", esc1.focus ? "✓" : "✗");
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(400);
  console.log("第二次Esc離開:", await eval_(`JSON.stringify(oc.focus)`) === "null" ? "✓" : "✗");

  /* ================= P15. 主畫布模式回饋 E7 =================
   * 建面工具:浮標(#canvasModeHint)+ crosshair 游標 + 狀態列頂點進度;
   * rect 單點 → toast;Esc → 清草稿+隱浮標;select → 全還原。 */
  console.log("=== P15. 主畫布模式回饋 E7 ===");
  const ocPt = await eval_(`(()=>{
    const r = document.getElementById("canvasViewport").getBoundingClientRect();
    for (const [fx, fy] of [[0.08,0.85],[0.5,0.9],[0.9,0.85],[0.9,0.2],[0.08,0.5]]) {
      const x = r.left + r.width*fx, y = r.top + r.height*fy;
      const el = document.elementFromPoint(x, y);
      if (el && el.closest("#ocv") && !el.closest(".ocard")) return {x, y};
    }
    return {x: r.left + r.width*0.5, y: r.top + r.height*0.9};
  })()`);
  /* (a) rect 工具:浮標 + crosshair */
  await eval_(`setOcTool("rect")`);
  await sleep(250);
  const mh1 = await eval_(`(()=>{const h=document.getElementById("canvasModeHint");
    return {vis:!h.hidden, txt:h.textContent,
      cur:getComputedStyle(document.getElementById("canvasViewport")).cursor};})()`);
  console.log("E7 rect 浮標:", mh1.vis && mh1.txt.includes("拖出範圍") ? "✓" : "✗ " + JSON.stringify(mh1),
    "| 游標:", mh1.cur === "crosshair" ? "✓" : "✗ " + mh1.cur);
  /* (b) rect 只點沒拖 → toast */
  await click(ocPt.x, ocPt.y);
  await sleep(400);
  const mhToast = await eval_(
    `[...document.querySelectorAll("#toastRegion .toast")].map(t=>t.textContent).join("|")`);
  console.log("E7 rect 單點 toast:", mhToast.includes("拖出範圍") ? "✓" : "✗ " + mhToast);
  /* (c) P 鍵(GEO-186 b):不再進入畫布繪圖工具——按一下即建預設外環的面卡、
     直接進入該面工作區並啟用「重畫外環」。 */
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "p", code: "KeyP", windowsVirtualKeyCode: 80 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "p", code: "KeyP", windowsVirtualKeyCode: 80 });
  await sleep(700);
  const mh2 = await eval_(`(()=>({
    faces: oc.faces.length,
    focus: oc.focus, tool: fe.tool,
    drawTool: oc.drawTool,
    hint: !document.getElementById("canvasModeHint").hidden}))()`);
  const mh2faces = await eval_(`api("objects").then(r=>r.faces.length)`);
  console.log("E7 P 鍵建面卡進面內:",
    mh2.faces === mh2faces && mh2.focus && mh2.focus.t === "face" && mh2.tool === "redraw"
      && !mh2.drawTool && !mh2.hint ? "✓" : "✗ " + JSON.stringify(mh2));
  /* (d) Esc 離開工作區回畫布(redraw 無草稿時一次 Esc 即返回) */
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(400);
  const mh3 = await eval_(`(()=>({
    focus: oc.focus,
    vis: !document.getElementById("canvasModeHint").hidden}))()`);
  console.log("E7 Esc 回畫布:", !mh3.focus && !mh3.vis ? "✓" : "✗ " + JSON.stringify(mh3));
  /* (e) 回選取 → 游標復原、浮標仍隱藏 */
  await eval_(`setOcTool("select")`);
  await sleep(200);
  const mh4 = await eval_(`(()=>({
    cur: getComputedStyle(document.getElementById("canvasViewport")).cursor,
    vis: !document.getElementById("canvasModeHint").hidden}))()`);
  console.log("E7 select 游標復原:", !mh4.vis && mh4.cur !== "crosshair" ? "✓" : "✗ " + JSON.stringify(mh4));

  /* ================= P16. 放置流程 F1/A7/A8 =================
   * #placeFlow 三步條、#placeValid u⊥v 即時驗證、預設卡、游離徽章捲動。 */
  console.log("=== P16. 放置流程條 + 放置表單 ===");
  await eval_(`(async()=>{
    await api("line reset");
    await api("line boundary 1 outline 0,0 3000,0 3000,2400 0,2400");
    await api("line canvas-pos boundary 1 80 80");
    await renderObjects();
    selectObject("boundary", 1);
  })()`);
  await sleep(500);
  /* (a) 游離面:流程條存在、步1 done、步2 current、限制說明 */
  const pf1 = await eval_(`(()=>{const f=document.getElementById("placeFlow");
    if(!f) return null;
    const st=[...f.querySelectorAll(".pf-step")].map(s=>s.className);
    return {steps:st,
      note: !!document.querySelector(".pf-note")};})()`);
  console.log("P16 流程條:", pf1 && pf1.steps[0].includes("done")
    && pf1.steps[1].includes("current") ? "✓ " + pf1.steps.join(",") : "✗ " + JSON.stringify(pf1),
    "| 游離說明:", pf1 && pf1.note ? "✓" : "✗");
  /* (b) u=+x v=+x → 禁用+錯誤訊息;u=+x v=+y → 解禁+法向 +Z */
  await eval_(`(()=>{
    const p=document.getElementById("inspectorContent");
    p.querySelector("#placeU").value="+x";
    p.querySelector("#placeV").value="+x";
    p.querySelector("#placeV").dispatchEvent(new Event("change"));
  })()`);
  const pv1 = await eval_(`(()=>({
    dis: document.querySelector("#placeSubmit").disabled,
    txt: document.getElementById("placeValid").textContent,
    cls: document.getElementById("placeValid").className}))()`);
  console.log("P16 平行禁用:", pv1.dis && pv1.txt.includes("垂直") && pv1.cls.includes("bad") ? "✓" : "✗ " + JSON.stringify(pv1));
  await eval_(`(()=>{
    const p=document.getElementById("inspectorContent");
    p.querySelector("#placeV").value="+y";
    p.querySelector("#placeV").dispatchEvent(new Event("change"));
  })()`);
  const pv2 = await eval_(`(()=>({
    dis: document.querySelector("#placeSubmit").disabled,
    txt: document.getElementById("placeValid").textContent}))()`);
  console.log("P16 垂直解禁:", !pv2.dis && pv2.txt.includes("+Z") ? "✓ " + pv2.txt : "✗ " + JSON.stringify(pv2));
  /* (c) 預設卡「天花」→ u=+x v=+y;送出後 placed + 步3亮 + 鈕文案「重綁」 */
  await eval_(`(()=>{
    const b=[...document.querySelectorAll("[data-place-preset]")]
      .find(x=>x.dataset.placePreset==="天花");
    if(b) b.click();
  })()`);
  const pv3 = await eval_(`(()=>({
    u: document.querySelector("#placeU").value,
    v: document.querySelector("#placeV").value}))()`);
  console.log("P16 預設卡:", pv3.u === "+x" && pv3.v === "+y" ? "✓" : "✗ " + JSON.stringify(pv3));
  await eval_(`document.querySelector("#placeSubmit").click()`);
  await sleep(700);
  const pf2 = await eval_(`(()=>{const f=document.getElementById("placeFlow");
    const o=ocFind("boundary",1);
    return {placed: !!o && !!o.placed,
      step3: f ? [...f.querySelectorAll(".pf-step")][2].className : "",
      btn: document.querySelector("#placeSubmit") ? document.querySelector("#placeSubmit").textContent : ""};})()`);
  console.log("P16 放置後:", pf2.placed ? "✓ placed" : "✗",
    "| 步3:", pf2.step3.includes("current") || pf2.step3.includes("done") ? "✓" : "✗ " + pf2.step3,
    "| 鈕:", pf2.btn.includes("更新放置") ? "✓" : "✗ " + pf2.btn);
  /* (d) 刪除鈕文案含 Ctrl+Z */
  const delTxt = await eval_(`document.getElementById("inspDelete").textContent`);
  console.log("P16 刪除文案:", delTxt.includes("Ctrl+Z") ? "✓" : "✗ " + delTxt);
  /* (e) 游離面:清單徽章點擊 → 檢視器捲到放置區 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line boundary 1 outline 0,0 2000,0 2000,1500 0,1500");
    await api("line canvas-pos boundary 1 60 60");
    await renderObjects();
  })()`);
  await sleep(500);
  const badgePos = await eval_(`(()=>{
    const b=[...document.querySelectorAll(".object-row .row-badge")][0];
    if(!b) return null; const r=b.getBoundingClientRect();
    return {x:r.left+r.width/2, y:r.top+r.height/2};})()`);
  if (badgePos) {
    await click(badgePos.x, badgePos.y);
    await sleep(600);
    const sc = await eval_(`(()=>{
      const t=document.querySelector("#inspectorContent .place-block")
           || document.getElementById("placeFlow");
      if(!t) return null; const r=t.getBoundingClientRect();
      return {top:r.top, ih:innerHeight};})()`);
    console.log("P16 徽章捲動:", sc && sc.top >= 0 && sc.top < sc.ih ? "✓" : "✗ " + JSON.stringify(sc));
  } else console.log("P16 徽章捲動: ✗ 找不到徽章");

  /* ================= P17. 主畫布其餘 A3-A6 A9-A11 F2 ================= */
  console.log("=== P17. 主畫布其餘 ===");
  /* (a) 物件庫:6 鈕 ≥50px、首格 btnBox6+建議起點 */
  const qc = await eval_(`(()=>{
    const g=[...document.querySelectorAll(".quick-create")];
    return {n:g.length, minH:Math.round(Math.min(...g.map(b=>b.getBoundingClientRect().height))),
      first:g[0].id, sug:g[0].textContent};})()`);
  console.log("P17 物件庫:", qc.n === 6 && qc.minH >= 50 && qc.first === "btnBox6"
    && qc.sug.includes("建議起點") ? "✓" : "✗ " + JSON.stringify(qc));
  /* (b) chips:關柱 → showColumn=false + aria-pressed;全部顯示還原 */
  await eval_(`document.querySelector('[data-filter-type="column"]').click()`);
  await sleep(300);
  const ch1 = await eval_(`(()=>({sc:oc.showColumn,
    ap:document.querySelector('[data-filter-type="column"]').getAttribute("aria-pressed")}))()`);
  console.log("P17 chip關柱:", !ch1.sc && ch1.ap === "false" ? "✓" : "✗ " + JSON.stringify(ch1));
  await eval_(`document.getElementById("filterAll").click()`);
  await sleep(300);
  const ch2 = await eval_(`oc.showColumn && oc.showFace && oc.showSpace && oc.showBeam`);
  console.log("P17 全部顯示:", ch2 ? "✓" : "✗");
  /* (c) compact:zoom 0.5 → .ocard.compact;1.0 → 無 */
  await eval_(`oc.zoom=0.5; ocApply()`);
  await sleep(250);
  const cp1 = await eval_(`document.querySelectorAll(".ocard.compact").length`);
  await eval_(`oc.zoom=1; ocApply()`);
  await sleep(250);
  const cp2 = await eval_(`document.querySelectorAll(".ocard.compact").length`);
  console.log("P17 compact:", cp1 > 0 && cp2 === 0 ? "✓" : `✗ ${cp1}/${cp2}`);
  /* (d) 邊樣式:包含實線 + 障礙虛線 + 中文標籤 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 10 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000");
    await api("line surface 11 origin 0 0 0 u +x v +z outline 0,0 4000,0 4000,2500 0,2500");
    await api("line space 1 boundary 10 11");
    await api("line column 1 in 1 at 1000 800 size 400 400 z 0 2500");
    await api("line canvas-pos space 1 60 60");
    await renderObjects();
  })()`);
  await sleep(600);
  const ed = await eval_(`(()=>{
    const items=[...document.querySelectorAll("#edgeGroup .edge-group-item")];
    return {n:items.length,
      dash:items.map(i=>i.querySelector(".edge-path").getAttribute("stroke-dasharray")),
      labels:[...document.querySelectorAll("#edgeLabelLayer .edge-label")].map(t=>t.textContent)};})()`);
  console.log("P17 連線:", ed.n >= 2 && ed.dash.includes("6 4") && ed.dash.includes("none")
    && ed.labels.includes("包含") && ed.labels.includes("障礙")
    ? "✓ " + ed.labels.join(",") : "✗ " + JSON.stringify(ed));
  /* (e) 空間卡語意槽 + footer 缺 */
  const sl = await eval_(`(()=>{
    const c=document.querySelector('.ocard[data-kind="space"]');
    return c ? c.textContent : "";})()`);
  console.log("P17 槽位語意:", sl.includes("天花") && !/\+X \d/.test(sl) ? "✓" : "✗ " + sl.slice(0, 100));
  console.log("P17 footer缺:", sl.includes("缺") ? "✓" : "✗ " + sl.slice(-40));
  /* (f) statusbar 32px + 摘要含物件 + 成功 toast.ok */
  const stb = await eval_(`(()=>({
    h:getComputedStyle(document.querySelector(".statusbar")).height,
    sum:document.getElementById("statusSummary").textContent}))()`);
  console.log("P17 狀態列:", stb.h === "32px" && stb.sum.includes("物件") ? "✓ " + stb.sum : "✗ " + JSON.stringify(stb));
  await eval_(`(async()=>{
    await emitLine("boundary 99 outline 0,0 500,0 500,400 0,400");
    await renderObjects();
  })()`);
  await sleep(400);
  const okN = await eval_(`document.querySelectorAll("#toastRegion .toast.ok").length`);
  console.log("P17 成功toast:", okN >= 1 ? "✓" : "✗");
  /* (g) snap/grid 鈕在 canvas-controls + aria-pressed;minimap 150+收合鈕 */
  const ctl = await eval_(`(()=>{
    const cc=document.querySelector(".canvas-controls");
    const st=document.getElementById("snapToggle"), gt=document.getElementById("gridToggle");
    const mm=document.querySelector(".minimap-shell");
    return {inCc: cc.contains(st) && cc.contains(gt),
      ap: st.getAttribute("aria-pressed") + "/" + gt.getAttribute("aria-pressed"),
      w: Math.round(mm.getBoundingClientRect().width),
      tog: !!document.getElementById("minimapToggle")};})()`);
  console.log("P17 畫布控制:", ctl.inCc && ctl.ap === "true/true" && ctl.w === 150 && ctl.tog
    ? "✓" : "✗ " + JSON.stringify(ctl));
  /* (h) gridToggle 關 → show-grid 消失;開回 */
  await eval_(`document.getElementById("gridToggle").click()`);
  await sleep(150);
  const g1 = await eval_(`document.getElementById("canvasViewport").classList.contains("show-grid")`);
  await eval_(`document.getElementById("gridToggle").click()`);
  await sleep(150);
  const g2 = await eval_(`document.getElementById("canvasViewport").classList.contains("show-grid")`);
  console.log("P17 格線切換:", !g1 && g2 ? "✓" : "✗");

  /* ================= P18. 面內工作區 B1-B9 =================
   * B1 工具鈕 icon+kbd、說明區移除;B2 分頁;B3 邊表;B4 zoom 適應格線;
   * B5 標註;B6 浮標限定;B7 #feApplyCard;B8 讀數;B9 麵包屑+膠囊。 */
  console.log("=== P18. 面內工作區 B1-B9 ===");
  await eval_(`(async()=>{
    await api("line reset");
    for (const ln of [
      "surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
      "surface 2 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000",
      "space 1 boundary 1 2",
      "column 1 in 1 at 1000 800 size 400 400 z 0 2500",
      "boundary 3 outline 0,0 500,0 500,400 0,400",
    ]) await api("line " + ln);
    await renderObjects();
    await enterFocus("face", 1);
  })()`);
  await sleep(900);
  /* (1) B1:工具鈕皆含 svg+kbd;說明區塊不存在 */
  const b1 = await eval_(`(()=>{
    const btns=[...document.querySelectorAll("[data-face-tool]")];
    const panel=document.querySelector(".face-layer-panel");
    return {n:btns.length,
      ok:btns.every(b=>b.querySelector("svg")&&b.querySelector("kbd")),
      noHelp:!panel.textContent.includes("說明")};})()`);
  console.log("P18 B1 工具icon+kbd:", b1.n >= 7 && b1.ok ? "✓" : `✗ n=${b1.n} ok=${b1.ok}`,
    "| 說明區已移除:", b1.noHelp ? "✓" : "✗");
  /* (2) B2:三頁;切角材 → tbA 可見 */
  const b2 = await eval_(`(()=>{
    const tabs=[...document.querySelectorAll("[data-fi-tab]")].map(t=>t.dataset.fiTab);
    document.querySelector('[data-fi-tab="timber"]').click();
    const tb=document.getElementById("tbA");
    return {tabs, vis: !!tb && tb.offsetParent !== null};})()`);
  console.log("P18 B2 四頁:", b2.tabs.join() === "prop,guide,timber,grid" ? "✓" : "✗ " + b2.tabs,
    "| 角材頁tbA可見:", b2.vis ? "✓" : "✗");
  /* (3) B3:邊表方向文字+mm+segmented */
  const b3 = await eval_(`(()=>{
    document.querySelector('[data-fi-tab="prop"]').click();
    /* §5.A.1.10 之後 #inspectorContent 也有一份同構 .edge-row(主畫布外環邊清單),
       這裡只驗面內右欄,scope 到 #faceInspectorContent 避免兩份互相命中(見 DOM-CONTRACT)。 */
    const scope=document.querySelector("#faceInspectorContent");
    const rows=[...scope.querySelectorAll(".edge-row")];
    return {n:rows.length,
      dir:rows.every(r=>/[→←↓↑]/.test(r.querySelector(".edge-dir").textContent)),
      mm:rows.every(r=>r.querySelector(".edge-mm").textContent.trim()==="mm"),
      seg:rows.every(r=>r.querySelectorAll(".fixity-btn").length===2),
      title:scope.querySelector(".ib-sub") && scope.querySelector(".ib-sub").textContent};})()`);
  console.log("P18 B3 邊表:", b3.n === 4 && b3.dir && b3.mm && b3.seg
    ? "✓" : `✗ ${JSON.stringify(b3)}`, "| 標題:", (b3.title||"").includes("固定") ? "✓" : "✗");
  /* (4) B4:zoom 0.17 → 螢幕格距≥24px、格線<60;zoom 2 → 檔位變小 */
  const b4a = await eval_(`(()=>{
    fe.zoom=0.17; feApplyZoom();
    const xs=[...document.querySelectorAll(".fe-grid-line")]
      .filter(l=>l.getAttribute("x1")===l.getAttribute("x2"))
      .map(l=>+l.getAttribute("x1")).sort((a,b)=>a-b);
    const uniq=[...new Set(xs)];
    let min=Infinity;
    for(let i=1;i<uniq.length;++i) min=Math.min(min,uniq[i]-uniq[i-1]);
    return {n:document.querySelectorAll(".fe-grid-line").length,
      gap:min*fe.zoom};})()`);
  console.log("P18 B4 zoom0.17:", b4a.gap >= 24 && b4a.n < 60
    ? `✓ gap=${b4a.gap.toFixed(1)}px n=${b4a.n}` : `✗ ${JSON.stringify(b4a)}`);
  const b4b = await eval_(`(()=>{
    fe.zoom=2; feApplyZoom();
    const xs=[...document.querySelectorAll(".fe-grid-line")]
      .filter(l=>l.getAttribute("x1")===l.getAttribute("x2"))
      .map(l=>+l.getAttribute("x1")).sort((a,b)=>a-b);
    const uniq=[...new Set(xs)];
    return uniq.length>1?uniq[1]-uniq[0]:0;})()`);
  console.log("P18 B4 zoom2檔位變小:", b4b === 25 ? "✓ g=25" : `✗ g=${b4b}`);
  /* (5) B5:邊長標註 + 原點標 */
  const b5 = await eval_(`(()=>{
    const dims=[...document.querySelectorAll(".fe-edge-dim")];
    const texts=[...document.querySelectorAll("#faceEditorRoot text")].map(t=>t.textContent);
    return {dimN:dims.length, dimOk:dims.every(d=>/^\\d+$/.test(d.textContent)),
      origin:texts.some(t=>t.includes("0,0 · u→ v↓")),
      guide:texts.some(t=>/^[uv] = -?\\d+$/.test(t))};})()`);
  console.log("P18 B5 邊長標註:", b5.dimN >= 4 && b5.dimOk ? `✓ n=${b5.dimN}` : `✗ ${JSON.stringify(b5)}`,
    "| 原點標:", b5.origin ? "✓" : "✗");
  /* (6) B6:select 隱藏、redraw 顯示 */
  const b6a = await eval_(`(()=>{
    document.querySelector('[data-face-tool="select"]').click();
    return document.getElementById("faceCanvasHint").hidden;})()`);
  await sleep(200);
  const b6b = await eval_(`(()=>{
    document.querySelector('[data-face-tool="redraw"]').click();
    return {h:document.getElementById("faceCanvasHint").hidden,
      t:document.getElementById("faceCanvasHint").textContent};})()`);
  console.log("P18 B6 浮標:select隱藏", b6a ? "✓" : "✗",
    "| redraw顯示", !b6b.h && b6b.t.includes("外環") ? "✓" : `✗ h=${b6b.h}`);
  await eval_(`document.querySelector('[data-face-tool="select"]').click()`);
  /* (7) B7:#feApplyCard + feCutStrip/feApplyProj;無 #b48 */
  const b7 = await eval_(`(()=>{
    const card=document.getElementById("feApplyCard");
    return {card:!!card,
      cut:card&&!!card.querySelector("#feCutStrip"),
      ap:card&&!!card.querySelector("#feApplyProj"),
      b48:!document.getElementById("b48"),
      noOld:!document.querySelector(".fe-ob-ctrl")};})()`);
  console.log("P18 B7 套用卡:", b7.card && b7.cut && b7.ap && b7.b48 && b7.noOld
    ? "✓" : "✗ " + JSON.stringify(b7));
  /* (8) B8:讀數格式 u N v N mm(指位移動後) */
  const b8vp = await eval_(`(()=>{const r=document.getElementById("faceEditorViewport").getBoundingClientRect();
    return {x:r.left+r.width/2,y:r.top+r.height/2};})()`);
  await send("Input.dispatchMouseEvent", { type:"mouseMoved", x:b8vp.x, y:b8vp.y });
  await sleep(250);
  const b8 = await eval_(`document.getElementById("faceCoordinateReadout").textContent`);
  console.log("P18 B8 讀數:", /^u \d+ v \d+ mm$/.test(b8) ? `✓ ${b8}` : `✗ ${b8}`);
  /* (9) B9:麵包屑完整格式「空間 1 / ● 面 1」(UI-REVIEW-SPEC §S3,非子字串)+ 天花膠囊;游離面→游離 */
  const b9a = await eval_(`({
    eb:document.getElementById("workspaceEyebrow").textContent,
    cap:document.getElementById("workspacePlaceTag").textContent,
    capCls:document.getElementById("workspacePlaceTag").className,
    back:document.getElementById("workspaceBackLabel").textContent})`);
  if (b9a && b9a.__err) console.log("P18 B9 麵包屑: ✗ eval", b9a.__err);
  else console.log("P18 B9 麵包屑:", b9a.eb === "空間 1 ›" ? "✓ " + b9a.eb : `✗ ${b9a.eb}`,
    "| 天花膠囊:", b9a.cap.includes("天花") ? "✓ " + b9a.cap : `✗ ${b9a.cap}`,
    "| 返回:", b9a.back.includes("物件畫布") ? "✓" : "✗");
  /* (10) 游離面:角材頁停用說明 + 游離膠囊 */
  await eval_(`enterFocus("face", 3)`);
  await sleep(700);
  const b9b = await eval_(`(()=>{
    document.querySelector('[data-fi-tab="timber"]').click();
    return {note:!!document.querySelector('[data-fi-pane="timber"] .fi-note'),
      cap:document.getElementById("workspacePlaceTag").textContent,
      tbDis:document.getElementById("tbA").disabled};})()`);
  console.log("P18 游離停用說明:", b9b.note && b9b.tbDis ? "✓" : "✗ " + JSON.stringify(b9b),
    "| 游離膠囊:", b9b.cap.includes("游離") ? "✓" : "✗ " + b9b.cap);
  /* (11) 狀態列右側快捷鍵 L/R/Esc */
  const b11 = await eval_(`(()=>{
    const ks=[...document.querySelectorAll(".ws-kbd-hints kbd")].map(k=>k.textContent);
    return {L:ks.includes("L"),R:ks.includes("R"),Esc:ks.includes("Esc")};})()`);
  console.log("P18 快捷鍵列:", b11.L && b11.R && b11.Esc ? "✓" : "✗ " + JSON.stringify(b11));
  await eval_(`(async()=>{ if(oc.focus) await leaveFocus(); })()`);
  await sleep(400);

  /* ================= P19. 空間工作區 C1-C5 + 三視圖 D1-D3 ================= */
  console.log("=== P19. 空間工作區 + 三視圖 ===");
  await eval_(`(async()=>{
    await api("line reset");
    for (const ln of [
      "surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
      "surface 2 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000",
      "space 1 boundary 1 2",
      "column 1 in 1 at 1000 800 size 400 400 z 0 2500",
      "column 2 at 5000 5000 size 400 400 z 0 2000",
      "boundary 3 outline 0,0 500,0 500,400 0,400",
    ]) await api("line " + ln);
    await renderObjects();
    await enterFocus("space", 1);
  })()`);
  await sleep(1200);
  /* (1) C1:兩頁切換 planSvg/projSvg 輪流可見;spaceFaceGrid 不存在 */
  const c1a = await eval_(`(()=>{
    const tabs=[...document.querySelectorAll("[data-ss-tab]")].map(t=>t.dataset.ssTab);
    const planVis=()=>!document.querySelector('[data-ss-pane="plan"]').hidden;
    const projVis=()=>!document.querySelector('[data-ss-pane="proj"]').hidden;
    const a=[planVis(),projVis()];
    document.querySelector('[data-ss-tab="proj"]').click();
    const b=[planVis(),projVis()];
    document.querySelector('[data-ss-tab="plan"]').click();
    return {tabs,a,b,grid:!!document.getElementById("spaceFaceGrid")};})()`);
  console.log("P19 C1 舞台分頁:", c1a.tabs.join() === "plan,proj" &&
    c1a.a[0] && !c1a.a[1] && !c1a.b[0] && c1a.b[1] ? "✓" : "✗ " + JSON.stringify(c1a),
    "| spaceFaceGrid移除:", !c1a.grid ? "✓" : "✗");
  /* (2) C4:構件列 .rc-act 可點(移出);刪除 toast 含 Ctrl+Z */
  const c4 = await eval_(`(()=>{
    const rows=[...document.querySelectorAll("#spaceRcList .rc-row")];
    const r=rows[0];
    return {n:rows.length, act:r && !!r.querySelector(".rc-act"),
      actTxt:r && r.querySelector(".rc-act").textContent,
      del:r && !!r.querySelector(".face-layer-del")};})()`);
  console.log("P19 C4 構件列動作鈕:", c4.n >= 1 && c4.act && c4.del
    ? `✓ ${c4.actTxt}` : "✗ " + JSON.stringify(c4));
  /* 點「移出」→ 構件游離;再「收進」 */
  const c4b = await eval_(`(async()=>{
    document.querySelector("#spaceRcList .rc-act").click();
    await new Promise(r=>setTimeout(r,800));
    const free1=document.querySelectorAll("#spaceRcFreeList .rc-row").length;
    document.querySelector("#spaceRcFreeList .rc-act").click();
    await new Promise(r=>setTimeout(r,800));
    const free2=document.querySelectorAll("#spaceRcFreeList .rc-row").length;
    const mine=document.querySelectorAll("#spaceRcList .rc-row").length;
    return {free1,free2,mine};})()`);
  console.log("P19 C4 移出/收進:", c4b.free1 === 2 && c4b.free2 === 1 && c4b.mine === 1
    ? "✓" : "✗ " + JSON.stringify(c4b));
  /* 刪除 → toast 含 Ctrl+Z */
  await eval_(`(async()=>{
    document.querySelector("#spaceRcFreeList .face-layer-del").click();
    await new Promise(r=>setTimeout(r,800));})()`);
  const c4c = await eval_(`[...document.querySelectorAll("#toastRegion .toast")]
    .map(t=>t.textContent).join("|")`);
  console.log("P19 C4 刪除toast含Ctrl+Z:", c4c.includes("Ctrl+Z") ? "✓" : "✗ " + c4c);
  /* (3) C3:槽位語意名+空槽「放置一片面」可點 */
  const c3 = await eval_(`(()=>{
    const rows=[...document.querySelectorAll("#spaceInspectorContent .slot-row")];
    return {n:rows.length,
      names:rows.map(r=>r.querySelector(".slot-name").textContent),
      axis:rows.every(r=>/[-+xyzXYZ=DW]/.test(r.querySelector(".slot-axis").textContent)),
      empty:rows.filter(r=>r.querySelector(".slot-empty")).length};})()`);
  console.log("P19 C3 槽位語意:", c3.n === 6 && c3.names.includes("天花")
    && c3.names.includes("前牆") && c3.axis ? "✓" : "✗ " + JSON.stringify(c3),
    "| 空槽鈕:", c3.empty >= 3 ? `✓ ${c3.empty}` : `✗ ${c3.empty}`);
  await eval_(`document.querySelector(".slot-empty").click()`);
  await sleep(800);
  const c3b = await eval_(`({focus:oc.focus && oc.focus.t==="face",
    toast:[...document.querySelectorAll("#toastRegion .toast")].map(t=>t.textContent).join("|")})`);
  console.log("P19 C3 空槽點擊有反應:", c3b.focus || c3b.toast.includes("預設")
    ? `✓ focus=${c3b.focus}` : "✗ " + JSON.stringify(c3b));
  await eval_(`(async()=>{ if(oc.focus) await leaveFocus(); await enterFocus("space",1); })()`);
  await sleep(800);
  /* (4) C5:#spProjRefresh 不存在;mutate(刪柱)後 spaceProjSvg 自動更新 */
  const c5 = await eval_(`(async()=>{
    const noBtn=!document.getElementById("spProjRefresh");
    const before=document.getElementById("spaceProjSvg").innerHTML.length;
    await emitLine("delete column 1");
    await new Promise(r=>setTimeout(r,900));
    const after=document.getElementById("spaceProjSvg").innerHTML.length;
    return {noBtn,before,after};})()`);
  console.log("P19 C5 無refresh鈕:", c5.noBtn ? "✓" : "✗",
    "| 自動更新:", c5.after !== c5.before ? `✓ ${c5.before}→${c5.after}` : `✗ ${c5.before}→${c5.after}`);
  await eval_(`(async()=>{ if(oc.focus) await leaveFocus(); })()`);
  await sleep(400);
  /* (5) D1:三視圖開 → 左 #v3Panel 視圖/圖層勾選;右 #v3PickPanel */
  await eval_(`document.getElementById("btnObj").click()`);
  await sleep(900);
  const d1 = await eval_(`(()=>{
    const vp=document.getElementById("v3Panel");
    return {vis: vp && !vp.hidden && vp.offsetParent !== null,
      views:document.querySelectorAll("[data-v3-view]").length,
      layers:document.querySelectorAll("[data-v3-layer]").length,
      pick:!document.getElementById("v3PickPanel").hidden};})()`);
  console.log("P19 D1 左欄視圖/圖層:", d1.vis && d1.views === 3 && d1.layers === 4
    ? "✓" : "✗ " + JSON.stringify(d1),
    "| 右欄pick容器:", d1.pick ? "✓" : "✗");
  /* (6) D2:#tool 非原生顯示(segmented)+三視圖縮放列 */
  const d2 = await eval_(`(()=>{
    const sel=document.getElementById("tool");
    const cs=getComputedStyle(sel);
    return {nativeHidden: +cs.opacity < 0.1 || cs.display === "none" ||
      sel.classList.contains("v3-native-select"),
      seg:document.querySelectorAll("[data-v3-tool]").length,
      segActive:document.querySelector("[data-v3-tool].active").dataset.v3Tool,
      /* 🔒 Q17(GEO-181):三視圖舊多邊形工具已移除,建多邊形面只走主畫布 P(PolyDraft) */
      noPoly:!document.querySelector('[data-v3-tool="poly"]') && !sel.querySelector('option[value="poly"]'),
      zoom:!!document.querySelector(".v3-zoom")};})()`);
  console.log("P19 D2 segmented:", d2.nativeHidden && d2.seg === 4 && d2.noPoly && d2.segActive === "view"
    ? "✓" : "✗ " + JSON.stringify(d2),
    "| 縮放列:", d2.zoom ? "✓" : "✗");
  /* segmented 切工具 → #tool 同步 */
  const d2b = await eval_(`(()=>{
    document.querySelector('[data-v3-tool="rect"]').click();
    return {tool:document.getElementById("tool").value,
      act:document.querySelector("[data-v3-tool].active").dataset.v3Tool};})()`);
  console.log("P19 D2 切工具同步:", d2b.tool === "rect" && d2b.act === "rect"
    ? "✓" : "✗ " + JSON.stringify(d2b));
  await eval_(`document.querySelector('[data-v3-tool="view"]').click()`);
  /* (7) D3:zoom 反比縮放——font-size(mm) 隨 zoom 反比,螢幕 px 不變 */
  const d3 = await eval_(`(()=>{
    const tx=document.querySelector("#world text[data-fs0]");
    if(!tx) return {none:true};
    const z0=zoom, fs0=+tx.getAttribute("font-size"), px0=fs0*transform().s;
    zoom=2; applyTransform();
    const fs2=+tx.getAttribute("font-size"), px2=fs2*transform().s;
    zoom=0.5; applyTransform();
    const fsH=+tx.getAttribute("font-size"), pxH=fsH*transform().s;
    zoom=z0; applyTransform();
    return {px0,px2,pxH};})()`);
  console.log("P19 D3 字級恆定:", d3.none ? "✗ 無文字" :
    (Math.abs(d3.px2 - d3.px0) < 0.5 && Math.abs(d3.pxH - d3.px0) < 0.5
      ? `✓ ${d3.px0.toFixed(1)}px 恆定` : `✗ ${JSON.stringify(d3)}`));
  /* (8) D1 圖層過濾生效:關掉「面」→ world 面元素減少 */
  const d1b = await eval_(`(async()=>{
    const before=document.querySelectorAll("#world polygon").length;
    document.querySelector('[data-v3-layer="face"]').click();
    await new Promise(r=>setTimeout(r,600));
    const after=document.querySelectorAll("#world polygon").length;
    document.querySelector('[data-v3-layer="face"]').click();
    await new Promise(r=>setTimeout(r,600));
    return {before,after};})()`);
  console.log("P19 D1 圖層過濾:", d1b.after < d1b.before
    ? `✓ ${d1b.before}→${d1b.after}` : `✗ ${JSON.stringify(d1b)}`);
  await eval_(`document.getElementById("btnCanvasView").click()`);
  await sleep(600);

  console.log("=== 10. 三視圖覆層再開 ===");
  await eval_(`document.getElementById("btnObj").click()`);
  await sleep(800);
  console.log("cv hidden:", await eval_(`document.getElementById("cv").hasAttribute("hidden")`));
  console.log("world children:", await eval_(`document.getElementById("world").childElementCount`));

  /* ================= Bugfix 2026-09-14 ================= */
  console.log("=== BF2. 一按就壞/會丟資料 ===");
  await eval_(`document.getElementById("btnCanvasView").click()`);
  await eval_(`api("line reset")`);
  await eval_(`api("line boundary 1 outline 0,0 4000,0 4000,3000 0,3000")`);
  await eval_(`api("line canvas-pos boundary 1 60 60")`);
  await eval_(`renderObjects()`);
  await sleep(800);
  /* (a) 「顯示全部」:ocFit() 無參數曾是 TypeError → 例外計數不得增加 */
  const exc0 = excN;
  await eval_(`document.getElementById("btnZoom").click()`);
  await sleep(500);
  console.log("BF2 btnZoom 無例外:", excN === exc0 ? "✓" : "✗ exc=" + (excN - exc0));
  /* (b) 放大鈕曾把 transform 變 NaN → 畫布消失 */
  await eval_(`document.getElementById("zoomInButton").click()`);
  await sleep(400);
  const tf = await eval_(`document.getElementById("oroot").getAttribute("transform")`);
  console.log("BF2 zoom transform:", tf, tf && !/NaN/.test(tf) ? "✓" : "✗");
  /* (c) /upload 後 curScene/標籤同步;btnScene 載回上傳內容,不載回 room_a */
  const fsB = require("fs"), osB = require("os"), pathB = require("path");
  const up = pathB.join(osB.tmpdir(), "verify-upload-bf.scene");
  fsB.writeFileSync(up, "boundary 1 outline 0,0 111,0 111,222 0,222\n");
  const doc = await send("DOM.getDocument");
  const fnode = await send("DOM.querySelector", { nodeId: doc.result.root.nodeId, selector: "#file" });
  await send("DOM.setFileInputFiles", { files: [up], nodeId: fnode.result.nodeId });
  await sleep(1500);
  const up1 = await eval_(`(async()=>({name:curScene.name,
    label:document.getElementById("sceneMenuLabel").textContent,
    mark:(await api("dump")).text.includes("111,222")}))()`);
  console.log("BF2 upload curScene:", JSON.stringify(up1),
    up1.name === "verify-upload-bf.scene" && up1.mark ? "✓" : "✗");
  await eval_(`loadScene(curScene.path,curScene.name)`);
  await sleep(1500);
  const up2 = await eval_(`(async()=>{const t=(await api("dump")).text;
    return {mark:t.includes("111,222"),roomA:t.includes("guide 1 1 v spec:主支1中線")}})()`);
  console.log("BF2 上傳場景重載不載回 room_a:", JSON.stringify(up2),
    up2.mark && !up2.roomA ? "✓" : "✗");
  /* (d) 換場景清焦點:enterFocus → loadScene → focus null、工作區關閉 */
  await eval_(`api("line reset")`);
  await eval_(`api("line boundary 1 outline 0,0 4000,0 4000,3000 0,3000")`);
  await eval_(`api("line placement 1 on boundary 1 origin 0 0 2500 u +x v +y")`);
  await eval_(`api("line canvas-pos boundary 1 60 60")`);
  await eval_(`renderObjects()`);
  await sleep(800);
  await eval_(`enterFocus("face",1)`);
  await sleep(800);
  const fpre = await eval_(`({focus:oc.focus && oc.focus.t,g:fe.guides.length})`);
  /* 路徑向 /scenes 取(伺服器端絕對路徑),不寫死——Windows 與 WSL 皆可跑。 */
  await eval_(`(async()=>{
    const list = await fetch("/scenes").then(r => r.json());
    const s = list.find(x => x.name === "room_a.scene");
    if (!s) throw new Error("/scenes 沒有 room_a.scene");
    return loadScene(s.path, s.name);
  })()`);
  await sleep(1800);
  const fpost = await eval_(`({focus:oc.focus,
    wsHidden:document.getElementById("objectWorkspace").hidden,
    guides:fe.guides.length,stack:oc.stack.length})`);
  console.log("BF2 換場景清焦點:", JSON.stringify(fpre), "→", JSON.stringify(fpost),
    fpre.focus === "face" && fpost.focus === null && fpost.wsHidden === true &&
    fpost.guides === 0 && fpost.stack === 0 ? "✓" : "✗");

  /* ================= BF3. undo 群組(L2) ================= */
  console.log("=== BF3. undo 群組 ===");
  /* 六面盒是 mutate 多行交易 → 一次 Ctrl+Z 應全退 */
  await eval_(`api("line reset")`);
  await eval_(`api("line boundary 1 outline 0,0 4000,0 4000,3000 0,3000")`);
  await eval_(`renderObjects()`);
  await sleep(600);
  const bf3pre = await eval_(`api("objects").then(r=>r.faces.length)`);
  await eval_(`document.getElementById("btnBox6").click()`);
  await sleep(300);
  await eval_(`document.getElementById("box6Submit").click()`);
  await sleep(1500);
  const bf3mid = await eval_(`api("objects").then(r=>r.faces.length)`);
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "z", code: "KeyZ", modifiers: 2, windowsVirtualKeyCode: 90 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "z", code: "KeyZ", modifiers: 2, windowsVirtualKeyCode: 90 });
  await sleep(1200);
  const bf3post = await eval_(`api("objects").then(r=>r.faces.length)`);
  console.log("BF3 六面盒一次 Ctrl+Z 全退:", bf3pre, "→", bf3mid, "→", bf3post,
    bf3mid === bf3pre + 6 && bf3post === bf3pre ? "✓" : "✗");

  /* ================= BF4. 其餘功能錯誤 ================= */
  console.log("=== BF4. 功能錯誤 ===");
  await eval_(`window.__apiLog = []; { const _a = api;
    api = c => { __apiLog.push(c); return _a(c); }; }`);
  /* (b) 六面盒排版避讓:既有卡佔 (60,60) 時,新卡不得同座標 */
  await eval_(`api("line reset")`);
  await eval_(`api("line boundary 1 outline 0,0 4000,0 4000,3000 0,3000")`);
  await eval_(`api("line canvas-pos boundary 1 60 60")`);
  await eval_(`renderObjects()`); await sleep(500);
  await eval_(`document.getElementById("btnBox6").click()`); await sleep(300);
  await eval_(`document.getElementById("box6Submit").click()`); await sleep(1500);
  const bf4dup = await eval_(`api("dump").then(r => {
    const seen = {}, dups = [];
    for (const l of r.text.split("\\n")) {
      const m = l.match(/^canvas-pos \\S+ \\d+ (-?\\d+) (-?\\d+)$/);
      if (m) { const k = m[1] + "," + m[2]; if (seen[k]) dups.push(k); seen[k] = 1; }
    }
    return dups; })`);
  console.log("BF4 六面盒排版無重疊:", JSON.stringify(bf4dup),
    bf4dup.length === 0 ? "✓" : "✗");
  /* (b2) GEO-157:六面盒不得覆寫既有物件。
     世界 boundary {1,2,5,9,MAX}、placement {MAX} → newid.boundary=3、newid.placement=0,
     舊算法 b0 = max(3,0) = 3,用掉 3,4,5,6,7,8——其中 5 已經存在,
     而 `surface` 對既有 id 是交易式重宣告＝**靜默覆寫**(狀態列照樣顯示 ✓)。
     修好之後會跳過 5,既有的 boundary 5 原封不動。 */
  for (const c of ["reset",
                   "surface 4294967295 origin 0 0 200 u +x v +y outline 0,0 100,0 100,100 0,100",
                   "boundary 9 outline 0,0 40,0 40,40 0,40",
                   "boundary 1 outline 0,0 50,0 50,50 0,50",
                   "boundary 2 outline 0,0 60,0 60,60 0,60",
                   "boundary 5 outline 0,0 90,0 90,90 0,90"]) {
    const result = await eval_(`api(${JSON.stringify("line " + c)})`);
    if (result?.ok !== true) throw new Error("BF4 夾具建立失敗: " + c + " " + JSON.stringify(result));
  }
  await eval_(`renderObjects()`); await sleep(500);
  await eval_(`document.getElementById("btnBox6").click()`); await sleep(300);
  await eval_(`document.getElementById("box6W").value = 4000;
               document.getElementById("box6D").value = 3000;
               document.getElementById("box6H").value = 2500;
               document.getElementById("box6Floor").checked = true;`);
  await eval_(`document.getElementById("box6Submit").click()`); await sleep(1500);
  const bf4keep = await eval_(`api("dump").then(r => {
    const rows = r.text.split("\\n");
    return { kept: rows.includes("boundary 5 outline 0,0 90,0 90,90 0,90"),
             faces: rows.filter(l => l.startsWith("boundary ")).length }; })`);
  console.log("BF4 六面盒不覆寫既有面(GEO-157):", JSON.stringify(bf4keep),
    bf4keep.kept && bf4keep.faces === 11 ? "✓" : "✗");
  /* (b3) GEO-157:0 沒被占用時也不能發給 surface(D4 的 boundary_id=0 是矩形標記)。 */
  const bf4zeroSeed = await eval_(`(async () => {
    const reset = await api("line reset");
    const seed = await api("line surface 4294967295 origin 0 0 200 u +x v +y outline 0,0 100,0 100,100 0,100");
    return reset.ok && seed.ok;
  })()`);
  await eval_(`renderObjects()`); await sleep(500);
  await eval_(`document.getElementById("btnBox6").click()`); await sleep(300);
  await eval_(`document.getElementById("box6W").value = 4000;
               document.getElementById("box6D").value = 3000;
               document.getElementById("box6H").value = 2500;
               document.getElementById("box6Floor").checked = true;`);
  await eval_(`document.getElementById("box6Submit").click()`); await sleep(1500);
  const bf4zero = await eval_(`(async () => {
    const dump = await api("dump"), objects = await api("objects");
    const rows = dump.text.split("\\n");
    return { kept: rows.includes("boundary 4294967295 outline 0,0 100,0 100,100 0,100"),
             faces: rows.filter(l => l.startsWith("boundary ")).length,
             spaces: objects.spaces.length, closed: objects.spaces[0]?.closed };
  })()`);
  console.log("BF4 六面盒回繞跳過保留編號0(GEO-157):", JSON.stringify(bf4zero),
    bf4zeroSeed === true && bf4zero.kept && bf4zero.faces === 7 &&
    bf4zero.spaces === 1 && bf4zero.closed ? "✓" : "✗");
  /* (b4) GEO-164:空間配號回繞也必須跳過 0 與已存在的空間 1。 */
  const bf4spaceSeed = await eval_(`api("line space 4294967295 boundary")`);
  if (bf4spaceSeed?.ok !== true) throw new Error("BF4 空間回繞夾具失敗: " + JSON.stringify(bf4spaceSeed));
  await eval_(`document.getElementById("btnBox6").click()`); await sleep(300);
  await eval_(`document.getElementById("box6W").value = 4000;
               document.getElementById("box6D").value = 3000;
               document.getElementById("box6H").value = 2500;
               document.getElementById("box6Floor").checked = true;`);
  await eval_(`document.getElementById("box6Submit").click()`); await sleep(1500);
  const bf4spaces = await eval_(`api("objects").then(r => r.spaces.map(s => ({id:s.id, closed:s.closed})))`);
  console.log("BF4 空間回繞跳過保留編號0及既有空間(GEO-164):", JSON.stringify(bf4spaces),
    bf4spaces.length === 3 && bf4spaces.some(s => s.id === 1 && s.closed) &&
    bf4spaces.some(s => s.id === 2 && s.closed) && bf4spaces.some(s => s.id === 4294967295) ? "✓" : "✗");
  /* (a) 空間示意圖 toRoom:點地板左上角內側 2px → 映射點(柱中心)應在角 100mm 內 */
  const bf4sp = await eval_(`api("objects").then(r => r.spaces[0] && r.spaces[0].id)`);
  await eval_(`enterFocus("space", ${bf4sp})`); await sleep(1000);
  const bf4pt = await eval_(`(() => {
    const f = document.querySelector("#spacePlanSvg .space-plan-floor");
    if (!f) return null;
    const r = f.getBoundingClientRect();
    return { x: r.x + 2, y: r.y + 2 }; })()`);
  await eval_(`window.__apiLog.length = 0`);
  if (bf4pt) await click(bf4pt.x, bf4pt.y);
  await sleep(1000);
  const bf4line = await eval_(`__apiLog.find(c => c.indexOf("column") >= 0) || ""`);
  const bf4m = /at (-?\d+) (-?\d+)/.exec(bf4line);
  /* at x y = 映射點 - 半柱邊(600/2=300);還原映射點驗證 ≈ 房角 (0,0) */
  const bf4px = bf4m && +bf4m[1] + 300, bf4py = bf4m && +bf4m[2] + 300;
  console.log("BF4 平面點放柱映射:", bf4line, "→ 映射點", bf4px + "," + bf4py,
    bf4m && Math.abs(bf4px) < 100 && Math.abs(bf4py) < 100 ? "✓" : "✗");
  /* (c) 面內 undo 刷新:刪 guide → 面內復原 → fe.guides 與 dump 一致 */
  await eval_(`leaveFocus()`); await sleep(400);
  await eval_(`api("line reset")`);
  await eval_(`api("line boundary 1 outline 0,0 4000,0 4000,3000 0,3000")`);
  await eval_(`api("line placement 1 on boundary 1 origin 0 0 2500 u +x v +y")`);
  await eval_(`(async()=>{await api("line spec 線位置 500"); await api("line guide 1 1 u spec:線位置")})()`);
  await eval_(`(async()=>{await api("line spec 線位置2 700"); await api("line guide 2 1 v spec:線位置2")})()`);
  await eval_(`renderObjects()`); await sleep(500);
  await eval_(`enterFocus("face",1)`); await sleep(800);
  await eval_(`api("line delete guide 2")`);
  await eval_(`feLoadGuides()`);            /* 同 UI 刪除後的快取狀態=1 */
  await eval_(`document.getElementById("faceUndoButton").click()`); await sleep(1200);
  const bf4g = await eval_(`(async () => ({ fe: fe.guides.length,
    dump: (await api("dump")).text.split("\\n").filter(l => /^guide /.test(l)).length }))()`);
  console.log("BF4 面內 undo 刷新:", JSON.stringify(bf4g),
    bf4g.fe === 2 && bf4g.dump === 2 ? "✓" : "✗");
  /* (e) Esc 在輸入框不關工作區:聚焦 .edge-len 按 Esc → 工作區仍開
     §5.A.1.10 之後 #inspectorContent 也有一份同構 .edge-len(主畫布外環邊清單,
     可能因 hidden 而 focus() 失敗),scope 到 #faceInspectorContent 避免誤命中。 */
  await eval_(`fiShowTab("prop")`); await sleep(300);
  const bf4hasLen = await eval_(`(() => {
    const i = document.querySelector("#faceInspectorContent .edge-len");
    if (i) { i.focus(); } return !!i && document.activeElement === i; })()`);
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(600);
  const bf4ws = await eval_(`document.getElementById("objectWorkspace").hidden`);
  console.log("BF4 Esc 輸入框不關工作區:", "focused=" + bf4hasLen, "wsHidden=" + bf4ws,
    bf4ws === false && bf4hasLen ? "✓" : "✗");
  /* (d) RC 表單驗證:x 留空 → 不送 column;w 留空 → 不送任何 line + 表單提示 */
  await eval_(`leaveFocus()`); await sleep(400);
  await eval_(`window.__apiLog.length = 0`);
  await eval_(`document.getElementById("btnNewColumn").click()`); await sleep(300);
  await eval_(`document.getElementById("rcX").value = ""`);
  await eval_(`document.getElementById("rcSubmit").click()`); await sleep(500);
  const bf4rc1 = await eval_(`__apiLog.filter(c => c.startsWith("line") || c === "newid")`);
  console.log("BF4 RC 空 x 不送指令:", JSON.stringify(bf4rc1),
    bf4rc1.length === 0 ? "✓" : "✗");
  await eval_(`window.__apiLog.length = 0;
    document.getElementById("rcW").value = ""; document.getElementById("rcX").value = "0"`);
  await eval_(`document.getElementById("rcSubmit").click()`); await sleep(500);
  const bf4rc2 = await eval_(`__apiLog.filter(c => c.startsWith("line") || c === "newid")`);
  const bf4err = await eval_(`!document.getElementById("rcErr").hidden`);
  console.log("BF4 RC 空 w 不送+表單提示:", JSON.stringify(bf4rc2),
    bf4rc2.length === 0 && bf4err ? "✓" : "✗");
  await eval_(`document.getElementById("rcCancel").click()`);

  /* ================= P20. 對抗審查漂移修正(A3 A4 A9 A10/A11 B1 B3 + toast/busy) =================
   * 對應 audit-A.md/audit-B.md 揪出的假完成項:斷言要咬住「修前」的錯誤做法。 */
  console.log("=== P20. 對抗審查漂移修正 ===");
  /* (a) A3:物件庫改 3 欄(repeat(3,1fr)),不是原 2 欄 */
  const p20a3 = await eval_(`getComputedStyle(document.querySelector(".quick-create-grid")).gridTemplateColumns`);
  const p20a3n = (p20a3 || "").trim().split(/\s+/).filter(Boolean).length;
  console.log("P20 A3 quick-create 3欄:", p20a3n === 3 ? `✓ ${p20a3}` : `✗ n=${p20a3n} (${p20a3})`);
  /* (b) A10/A11:minimapToggle 熱區 ≥28×28(原 20×20) */
  const p20a10 = await eval_(`(()=>{const r=document.getElementById("minimapToggle").getBoundingClientRect();
    return {w:Math.round(r.width),h:Math.round(r.height)};})()`);
  console.log("P20 A10 minimapToggle熱區≥28:", p20a10.w >= 28 && p20a10.h >= 28
    ? `✓ ${p20a10.w}×${p20a10.h}` : `✗ ${JSON.stringify(p20a10)}`);
  /* (c) toast 避讓小地圖:.toast-region bottom ≥ 118(14+96+8),原 42 會被小地圖蓋住 */
  const p20tr = await eval_(`parseFloat(getComputedStyle(document.querySelector(".toast-region")).bottom)`);
  console.log("P20 toast避讓小地圖:", p20tr >= 118 ? `✓ bottom=${p20tr}px` : `✗ bottom=${p20tr}px`);
  /* (d) 建物件:free 面(boundary 3)+ space(1,由已放置 boundary 1/2 組成,帶 guide)供 A4/B1/B3 用 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    await api("line surface 2 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000");
    await api("line space 1 boundary 1 2");
    await api("line spec 線位置 500"); await api("line guide 1 1 u spec:線位置");
    await api("line boundary 3 outline 0,0 500,0 500,400 0,400");
    await api("line canvas-pos boundary 3 500 60");
    await api("line canvas-pos space 1 60 60");
    await renderObjects();
  })()`);
  await sleep(700);
  /* (e) A4:faceCard()/spaceCard() 卡片標題 font-size 12.5(原 11.5) */
  const p20a4 = await eval_(`(()=>{
    const fc = document.querySelector('.ocard[data-kind="boundary"] text');
    const sc = document.querySelector('.ocard[data-kind="space"] text');
    return {f: fc && fc.getAttribute("font-size"), s: sc && sc.getAttribute("font-size")};})()`);
  console.log("P20 A4 卡片標題12.5:", p20a4.f === "12.5" && p20a4.s === "12.5"
    ? "✓" : `✗ ${JSON.stringify(p20a4)}`);
  /* (f) A9:成功 toast 的 .toast.ok svg 著色 = --face(原無 .toast.ok 規則) */
  await eval_(`(async()=>{ await emitLine("boundary 77 outline 0,0 300,0 300,300 0,300"); await renderObjects(); })()`);
  await sleep(400);
  const p20a9 = await eval_(`(()=>{
    const svg = document.querySelector("#toastRegion .toast.ok svg");
    if (!svg) return null;
    const got = getComputedStyle(svg).color;
    const probe = document.createElement("span");
    probe.style.color = "var(--face)";
    document.body.appendChild(probe);
    const want = getComputedStyle(probe).color;
    probe.remove();
    return {got, want};})()`);
  console.log("P20 A9 toast.ok著色:", p20a9 && p20a9.got === p20a9.want
    ? `✓ ${p20a9.got}` : `✗ ${JSON.stringify(p20a9)}`);
  /* (g) B1:面內圖層列 .face-layer-icon 一律 svg,不含 ▱▨⌖▤╬ 純文字 */
  await eval_(`enterFocus("face", 1)`);
  await sleep(700);
  await eval_(`fiShowTab("prop")`);
  await sleep(200);
  /* 範圍限定 #faceLayerList(renderFaceLayers() 的圖層列),避開 #workspaceTypeIcon
     這個同名 class 但語意無關的頂列型別圖示(index.html 靜態標記,非 B1 範圍) */
  const p20b1 = await eval_(`(()=>{
    const icons = [...document.querySelectorAll("#faceLayerList .face-layer-icon")];
    return {n: icons.length,
      svgN: icons.filter(i => i.querySelector("svg")).length,
      bad: icons.some(i => /[▱▨⌖▤╬]/.test(i.textContent))};})()`);
  console.log("P20 B1 圖層列SVG圖示:", p20b1.n >= 1 && p20b1.svgN === p20b1.n && !p20b1.bad
    ? `✓ n=${p20b1.n}` : `✗ ${JSON.stringify(p20b1)}`);
  /* (h) B3:.fixity-btn.seg 熱區高度 ≥28(原 22) */
  const p20b3 = await eval_(`(()=>{
    const btns = [...document.querySelectorAll(".fixity-btn.seg")];
    return {n: btns.length,
      minH: btns.length ? Math.min(...btns.map(b => b.getBoundingClientRect().height)) : 0};})()`);
  console.log("P20 B3 fixity-btn熱區≥28:", p20b3.n >= 1 && p20b3.minH >= 28
    ? `✓ n=${p20b3.n} minH=${p20b3.minH}` : `✗ ${JSON.stringify(p20b3)}`);
  await eval_(`leaveFocus()`);
  await sleep(400);
  /* (i) v2:短操作不閃動;超過 400 ms 才顯示進度,結束收起。 */
  const p20busy = await eval_(`(async () => {
    const original = api;
    let delayed = false;
    api = async cmd => { if (!delayed) { delayed=true; await new Promise(r=>setTimeout(r,800)); } return original(cmd); };
    try {
      const p = mutate(["boundary 555 outline 0,0 10,0 10,10 0,10"]);
      const early = document.getElementById("busyIndicator").hidden;
      await new Promise(r=>setTimeout(r,500));
      const mid = document.getElementById("busyIndicator").hidden;
      const opacity = getComputedStyle(document.querySelector('.workspace')).opacity;
      await p;
      return {early, mid, after:document.getElementById("busyIndicator").hidden, opacity};
    } finally { api=original; }
  })()`);
  console.log("P20 busy指示:", p20busy.early && !p20busy.mid && p20busy.after && p20busy.opacity === '1'
    ? "✓" : `✗ ${JSON.stringify(p20busy)}`);
  /* (j) §S1 全域最小字級 11px:主畫布／面內／空間工作區三畫面全掃描,
     不得有任何可見元素 computed font-size < 11px。
     排除:①未顯示元素(如空的 .toast-region)因寬高為 0 自然排除,不需另立白名單;
     ②SVG 命名空間下畫布繪製的 <text>/<tspan>(卡片副標、狀態膠囊「游離/無邊界」、
     空間卡槽位軸標、面內原點座標標註)——這些數值由 §S2 明文另訂
     (「副標 10.5＋狀態膠囊 10.5」),不屬 §S1『元件最小 11px』規範對象,
     此處明文排除、非隨意放寬。 */
  await eval_(`window.__scanMinFont = () => {
    let min = Infinity, sel = "";
    for (const el of document.querySelectorAll("body *")) {
      if (el.namespaceURI === "http://www.w3.org/2000/svg") continue;
      const cs = getComputedStyle(el);
      if (cs.display === "none" || cs.visibility === "hidden") continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      const fs = parseFloat(cs.fontSize);
      if (fs && fs < min) { min = fs;
        sel = (el.id ? "#" + el.id : "") + (el.className ? "." + String(el.className).split(" ")[0] : "") || el.tagName; }
    }
    return {min, sel};
  }`);
  const p20fontMain = await eval_(`__scanMinFont()`);
  await eval_(`enterFocus("face", 1)`);
  await sleep(500);
  const p20fontFace = await eval_(`__scanMinFont()`);
  await eval_(`(async()=>{ await leaveFocus(); await enterFocus("space", 1); })()`);
  await sleep(500);
  const p20fontSpace = await eval_(`__scanMinFont()`);
  const p20fontAll = [["主畫布", p20fontMain], ["面內", p20fontFace], ["空間工作區", p20fontSpace]];
  const p20fontBad = p20fontAll.filter(([, v]) => !(v.min >= 11));
  console.log("P20 全域最小字級≥11px:", p20fontBad.length === 0
    ? `✓ ${p20fontAll.map(([n, v]) => `${n}=${v.min}`).join(" ")}`
    : `✗ ${p20fontBad.map(([n, v]) => `${n}: min=${v.min}px @ ${v.sel}`).join("; ")}`);
  /* (k) B-icon:.space-member-thumb 無承載面(bmap 缺失)時走 icon("rectangle")
     SVG 佔位,不留 ▱▨⌖▤╬ 等 Unicode 圖示字元。目前處於空間 1 工作區
     (成員 1 2 皆已放置、bmap 皆有值),故先人為刪除成員 2 的 bmap 條目
     模擬「無承載面資料」情形,重繪縮圖列後檢查該格內容。 */
  const p20thumb = await eval_(`(async()=>{
    delete oc.bmap[2];
    await renderSpaceWorkspace();
    const rows = [...document.querySelectorAll(".space-member-thumb")];
    return {n: rows.length,
      bad: rows.some(t => /[▱▨⌖▤╬]/.test(t.textContent)),
      svgN: rows.filter(t => t.querySelector("svg")).length};})()`);
  console.log("P20 space-member-thumb無殘留Unicode圖示:", p20thumb.n >= 1 && !p20thumb.bad && p20thumb.svgN === p20thumb.n
    ? `✓ n=${p20thumb.n} svgN=${p20thumb.svgN}` : `✗ ${JSON.stringify(p20thumb)}`);
  await eval_(`leaveFocus()`);
  await sleep(400);

  /* ================= P21. 對抗審查漂移修正(C1 C3 C4 D2) =================
   * 對應 audit-CD.md 揪出的 PARTIAL 項:C1 佔滿高度、C3 空槽直達放置、
   * C4 移出/收進鈕熱區、D2 縮放列移左下。斷言要咬住「修前」的錯誤做法。 */
  console.log("=== P21. 對抗審查漂移修正(空間工作區/三視圖) ===");
  /* (a) C1:空間工作區「平面示意」舞台內容高度 ≥ 可用高度 85%,且無捲軸 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    await api("line space 1 boundary 1");
    await api("line canvas-pos space 1 60 60");
    await renderObjects();
    await enterFocus("space", 1);
  })()`);
  await sleep(600);
  const p21c1 = await eval_(`(()=>{
    const stage = document.querySelector(".space-workspace-stage");
    const strip = document.querySelector(".space-plan-strip");
    if (!stage || !strip) return null;
    const sr = stage.getBoundingClientRect(), cr = strip.getBoundingClientRect();
    return { ratio: +(cr.height / sr.height).toFixed(3),
      overflow: stage.scrollHeight > stage.clientHeight + 2,
      sh: Math.round(sr.height), ch: Math.round(cr.height) };
  })()`);
  console.log("P21 C1 舞台佔滿高度:", p21c1 && p21c1.ratio >= 0.85 && !p21c1.overflow
    ? `✓ ratio=${p21c1.ratio} h=${p21c1.ch}/${p21c1.sh}` : `✗ ${JSON.stringify(p21c1)}`);

  /* (b) C3:空槽點擊直達放置——帶入槽位對應預設 u/v,且選中的是預期的游離面 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000");
    await api("line space 1 boundary 1");
    await api("line boundary 10 outline 0,0 400,0 400,300 0,300");
    await api("line canvas-pos space 1 60 60");
    await api("line canvas-pos boundary 10 400 60");
    await renderObjects();
    await enterFocus("space", 1);
  })()`);
  await sleep(600);
  const p21c3click = await eval_(`(()=>{
    const b = [...document.querySelectorAll(".slot-empty")]
      .find(x => x.dataset.slotLabel === "地板");
    if (!b) return false;
    b.click();
    return true;
  })()`);
  await sleep(700);
  const p21c3 = await eval_(`(()=>{
    const p = document.getElementById("faceInspectorContent");
    const u = p && p.querySelector("#placeU"), v = p && p.querySelector("#placeV");
    return { clicked: true, focus: oc.focus && JSON.parse(JSON.stringify(oc.focus)),
      u: u && u.value, v: v && v.value };
  })()`);
  console.log("P21 C3 空槽直達放置:",
    p21c3click && p21c3.focus && p21c3.focus.t === "face" && p21c3.focus.id === 10 &&
    p21c3.u === "+y" && p21c3.v === "+x"
      ? `✓ face=${p21c3.focus.id} u=${p21c3.u} v=${p21c3.v}` : `✗ ${JSON.stringify(p21c3)}`);
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* (c) C4:構件列「移出/收進」鈕熱區 ≥28px,與旁邊 ✕ 一致
     柱需落在一個有地板足跡的空間內才會生效,否則核心回「空間不存在」。 */
  await eval_(`(async()=>{
    await api("line reset");
    await api("line surface 1 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000");
    await api("line space 1 boundary 1");
    await api("line canvas-pos space 1 60 60");
    await api("line column 5 in 1 at 0 0 size 600 600 z 0 2500");
    await renderObjects();
    await enterFocus("space", 1);
  })()`);
  await sleep(600);
  const p21c4 = await eval_(`(()=>{
    const b = document.querySelector(".rc-act");
    return b ? Math.round(b.getBoundingClientRect().height) : null;
  })()`);
  console.log("P21 C4 rc-act熱區≥28:", p21c4 !== null && p21c4 >= 28
    ? `✓ h=${p21c4}` : `✗ ${JSON.stringify(p21c4)}`);
  await eval_(`leaveFocus()`);
  await sleep(300);

  /* (d) D2:三視圖縮放列獨立於左下,不在 #viewToolbar 內 */
  await eval_(`document.getElementById("btnObj").click()`);
  await sleep(600);
  const p21d2 = await eval_(`(()=>{
    const canvas = document.getElementById("canvasViewport").getBoundingClientRect();
    const bar = document.querySelector(".v3-zoom");
    if (!bar) return null;
    const bb = bar.getBoundingClientRect();
    return { left: Math.round(bb.left - canvas.left),
      bottom: Math.round(canvas.bottom - bb.bottom),
      inToolbar: !!bar.closest("#viewToolbar") };
  })()`);
  console.log("P21 D2 縮放列移左下:",
    p21d2 && p21d2.left < 100 && p21d2.bottom < 60 && !p21d2.inToolbar
      ? `✓ ${JSON.stringify(p21d2)}` : `✗ ${JSON.stringify(p21d2)}`);
  await eval_(`document.getElementById("btnCanvasView").click()`);
  await sleep(300);

  /* ================= P22. #inspDelete 對齊 C4(不彈 confirm,toast+可 Ctrl+Z 復原) =================
   * 對抗審查指認:主畫布/RC 檢視器 #inspDelete 仍走 confirm(),與空間工作區
   * renderSpaceRc 構件列 ✕(C4:直接刪除+toast)不一致。 */
  console.log("=== P22. #inspDelete 對齊 C4 ===");
  await eval_(`(async()=>{
    await api("line reset");
    await api("line boundary 41 outline 0,0 1000,0 1000,800 0,800");
    await api("line canvas-pos boundary 41 60 60");
    await renderObjects();
    selectObject("boundary", 41);
  })()`);
  await sleep(500);
  /* (a) 裝 confirm 監聽 spy(不覆寫成通過,只記錄有沒有被呼叫)→ 點刪除鈕 → 物件即消失 */
  await eval_(`window.__confirmCalled = false;
    window.confirm = () => { window.__confirmCalled = true; return true; };`);
  await eval_(`document.getElementById("inspDelete").click()`);
  await sleep(700);
  const p22a = await eval_(`api("objects").then(r=>({
    called: window.__confirmCalled, gone: !r.faces.some(f=>f.id===41)}))`);
  console.log("P22 不彈confirm+直接刪除:", !p22a.called && p22a.gone
    ? "✓" : `✗ ${JSON.stringify(p22a)}`);
  /* (b) toast 提示可復原 */
  const p22b = await eval_(`(()=>{
    const ts=[...document.querySelectorAll("#toastRegion .toast")];
    const t=ts[ts.length-1];
    return t ? t.textContent : null;
  })()`);
  console.log("P22 toast含復原字樣:", p22b && (p22b.includes("復原") || p22b.includes("Ctrl+Z"))
    ? `✓ ${p22b}` : `✗ ${p22b}`);
  /* (c) Ctrl+Z 一次整組復原(boundary 41 沒有 placement,delete 只有一行,仍走同一 mutate 機制) */
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "z", code: "KeyZ", modifiers: 2, windowsVirtualKeyCode: 90 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "z", code: "KeyZ", modifiers: 2, windowsVirtualKeyCode: 90 });
  await sleep(800);
  const p22c = await eval_(`api("objects").then(r=>r.faces.some(f=>f.id===41))`);
  console.log("P22 Ctrl+Z復原:", p22c ? "✓" : `✗ ${p22c}`);

  const gridRefUi = await eval_(`(async()=>{
    resetSceneFocus();
    const lines = [
      "reset",
      "surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
      "grid 1 on 1 u 2000",
      "timber 2 20 20 role boundary",
      "timber 3 20 20 role boundary",
      "place 2 on 1 at-face e0 +u +n",
      "place 3 on 1 at-face e2 -u +n",
      "timber 1 27 33 role primary",
      "place 1 on 1 at-line grid 1 u 0 +v +n"
    ];
    for (const line of lines) {
      const r = await api("line " + line);
      if (!r.ok) return {error:r.error};
    }
    await renderObjects();
    await enterFocus("face", 1);
    const before = fe.timbers.find(t => t.id === 1);
    const saved = (await api("dump")).text;
    const uploaded = await fetch("/upload", {method:"POST", body:saved}).then(r=>r.json());
    if (!uploaded.ok) return {error:uploaded.error};
    resetSceneFocus();
    await renderObjects();
    await enterFocus("face", 1);
    const after = fe.timbers.find(t => t.id === 1);
    const locked = await apiRequest("line grid 1 on 1 u 1500");
    await apiRequest("line cancel-preview");
    return {before,after,hasRef:saved.includes("at-line grid 1 u 0"),
            locked:!locked.ok && locked.preview?.valid};
  })()`);
  const gridRefUiOk = gridRefUi && gridRefUi.hasRef && gridRefUi.locked &&
    gridRefUi.before && gridRefUi.before.L === 2960 &&
    JSON.stringify(gridRefUi.before) === JSON.stringify(gridRefUi.after);
  if (gridRefUiOk) passN++; else failN++;
  _log("P23 grid-ref 存檔上傳後足跡與引用鎖:", gridRefUiOk ? "PASS" : "FAIL", JSON.stringify(gridRefUi));

  }
  { // P24–P32 使用獨立作用域，避免與既有測試的輔助函式同名。
  const check = (name, ok, detail = '') => console.log(name, ok ? '✓' : '✗', JSON.stringify(detail));
  const waitIdle = async () => {
    for (let i=0;i<100;i++) {
      if (await eval_('!oc.busy && !dragging')) return;
      await sleep(50);
    }
    throw Error('UI did not finish transaction');
  };
  const clickSelector = async sel => {
    const p = await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,hit=document.elementFromPoint(x,y);return {x,y,hit:e.contains(hit),target:hit?.outerHTML?.slice(0,200)}})()`);
    if (!p.hit) throw Error('Control is not reachable '+sel+' '+JSON.stringify(p));
    await click(p.x,p.y); await sleep(120); await waitIdle();
  };
  const setupRemaining = async lines => {
    const out = await eval_(`(async()=>{await setView3(false);resetSceneFocus();await api('reset');const out=[];for(const s of ${JSON.stringify(lines)})out.push(await api('line '+s));await renderObjects();return out})()`);
    if (!Array.isArray(out) || out.some(r=>!r.ok)) throw Error('test setup failed '+JSON.stringify(out));
  };
  const remainingShot = async name => {
    const dest=process.env.GEOMETRY_REPAIR_SCREENSHOT_DIR;
    if (!dest) return;
    const r=await send('Page.captureScreenshot',{format:'png'});
    require('fs').writeFileSync(require('path').join(dest,name+'.png'),Buffer.from(r.result.data,'base64'));
  };
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
  check('P24 page identity',await eval_(`location.href === ${JSON.stringify(process.env.GEOMETRY_TEST_URL || 'http://localhost:8765/')} && document.title.length>0 && document.querySelectorAll('button').length>10 && !document.querySelector('vite-error-overlay,nextjs-portal')`));

  if (!process.env.GEOMETRY_UI_REVIEW_ONLY) {
  for (const axis of ['x','y']) for (const center of [-100,-1,0,100]) for (const width of [300,301]) {
    await setupRemaining([`beam 1 along ${axis} from 0 to 1000 at ${center} width ${width} depth 100 top 1000`]);
    await eval_(`selectObject('beam',1)`);
    const before=await eval_(`(async()=>({box:(await api('objects')).beams[0].box,c:+document.querySelector('#rcfC').value,hasApply:!!document.querySelector('#rcfApply')}))()`);
    const shifted=center+40;
    await eval_(`document.querySelector('#rcfC').value=${JSON.stringify(String(shifted))}`);
    await clickSelector('#rcfApply');
    const after=await eval_(`api('objects').then(r=>r.beams[0].box)`);
    const gotC=axis==='x' ? after[1]+Math.floor((after[4]-after[1])/2) : after[0]+Math.floor((after[3]-after[0])/2);
    check(`P25 beam ${axis}/${center}/${width}`,before.hasApply && before.c===center && gotC===shifted,{before,after,gotC,shifted});
  }

  const outer=['0,0','4000,0','4000,3000','0,3000'];
  const hole=['500,500','1500,500','1500,1500','500,1500'];
  for (const ro of [false,true]) for (const rh of [false,true]) {
    await setupRemaining(['boundary 1 outline '+(ro?[...outer].reverse():outer).join(' ')+' hole '+(rh?[...hole].reverse():hole).join(' ')]);
    await eval_(`enterFocus('face',1)`);
    const text=await eval_(`document.querySelector('#faceInspectorContent').innerText`);
    check(`P26 hole area outer=${ro} hole=${rh}`,text.includes('11.00 m²'),text.match(/面積[^\n]*\n[^\n]*/)?.[0]);
  }
  await remainingShot('hole-area');

  await setupRemaining(['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000', 'spec 起點 300', 'spec 目標 900', 'spec 再移 1200', 'guide 1 1 u spec:起點']);
  await eval_(`(async()=>{await setView3(true);await render()})()`);
  const initial=(await eval_(`api('dump')`)).text;
  const points=await eval_(`(async()=>{const a=[];for(const v of [300,900,1200]){const p=await api('proj 2 2500 '+v+' 1');const t=transform(),r=cv.getBoundingClientRect(),l=layout.views[2];a.push({x:r.left+t.ox+(p.x+l.tx)*t.s,y:r.top+t.oy+(p.y+l.ty)*t.s});}return a})()`);
  await drag(points[0].x,points[0].y,points[1].x,points[1].y,8);
  await waitIdle();
  const moved=(await eval_(`api('dump')`)).text;
  check('P27 real guide drag changed model',initial!==moved && /guide 1 1 u spec:目標/.test(moved));
  const key = async redo => {
    for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key:'z',code:'KeyZ',windowsVirtualKeyCode:90,modifiers:redo?10:2});
    await sleep(200);await waitIdle();
  };
  await key(false);
  check('P27 one Ctrl+Z restores whole gesture',(await eval_(`api('dump')`)).text===initial);
  await key(true);
  check('P27 Ctrl+Shift+Z redoes whole gesture',(await eval_(`api('dump')`)).text===moved);
  await send('Input.dispatchMouseEvent',{type:'mousePressed',...points[1],button:'left',clickCount:1});
  await sleep(100);
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',...points[2],button:'left',buttons:1});
  await sleep(100);
  const mid=(await eval_(`api('dump')`)).text;
  const engaged=await eval_(`!!(dragging && dragging.started && dragging.guide>=0)`);
  check('P27 cancel drag engaged',engaged && mid===moved,{engaged,mid});
  await eval_(`cv.dispatchEvent(new PointerEvent('pointercancel',{bubbles:true,cancelable:true,pointerId:1}))`);
  await send('Input.dispatchMouseEvent',{type:'mouseReleased',...points[2],button:'left',clickCount:1});
  await waitIdle();
  check('P27 cancelled drag restores model',(await eval_(`api('dump')`)).text===moved);
  // A quick click must not leave an open transaction or consume an undo step.
  await click(points[1].x,points[1].y);await waitIdle();await key(false);
  check('P27 quick click keeps prior undo',(await eval_(`api('dump')`)).text===initial);

  for (const scope of ['face','space']) {
    await setupRemaining(['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
                          'spec 起點 300', 'spec 目標 900', 'guide 1 1 u spec:起點', 'space 1 boundary 1']);
    await eval_(`enterFocus('${scope}',1)`);
    await clickSelector(scope==='face' ? '#projToggle' : '[data-ss-tab="proj"]');
    await sleep(200);
    const pp=await eval_(`(async()=>{
      const svg='${scope}'==='face' ? document.querySelector('#projViews [data-view="2"]').closest('svg') : document.querySelector('#spaceProjSvg');
      svg.scrollIntoView({block:'center'});
      const L=(await api('render')).layout.views[2];
      const out=[];
      for(const v of [300,900]) {
        const p=await api('proj 2 2500 '+v+' 1'),q=svg.createSVGPoint();
        q.x=p.x+('${scope}'==='space'?L.tx:0);q.y=p.y+('${scope}'==='space'?L.ty:0);
        const c=q.matrixTransform(svg.getScreenCTM());out.push({x:c.x,y:c.y});
      }
      return out;
    })()`);
    if (!Array.isArray(pp)) { check('P27 '+scope+' projection setup',false,pp); continue; }
    const start=(await eval_(`api('dump')`)).text;
    await drag(pp[0].x,pp[0].y,pp[1].x,pp[1].y,6);await waitIdle();
    const after=(await eval_(`api('dump')`)).text;
    check('P27 '+scope+' projection drag',after!==start && /guide 1 1 u spec:目標/.test(after),{points:pp,changed:after!==start,guide:after.match(/guide 1[^\n]+/g)});
    await key(false);
    check('P27 '+scope+' projection one-step undo',(await eval_(`api('dump')`)).text===start);
  }

  for (const width of [1400,1160]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    await setupRemaining(['boundary 99 outline 0,0 100,0 100,100 0,100']);
    await eval_(`closeMenus()`);
    await clickSelector('#fileMenuBtn');
    const hit=await eval_(`(()=>{const e=document.querySelector('#btnEx'),r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))})()`);
    check('P28 file menu hit target @'+width,hit);
    await remainingShot('file-menu-'+width);
    await clickSelector('#btnEx');
    let loaded;
    for (let i=0;i<100;i++) {
      loaded=await eval_(`({path:curScene.path,name:curScene.name,status:document.querySelector('#status').textContent,ids:oc.faces.map(f=>f.id)})`);
      if (loaded.status.includes('已載入') && loaded.ids.includes(1) && !loaded.ids.includes(99)) break;
      await sleep(50);
    }
    check('P29 example loads from web directory @'+width,loaded.name==='room_a.scene' && loaded.path!=='room_a.scene' && loaded.ids.includes(1) && !loaded.ids.includes(99) && loaded.status.includes('已載入'),loaded);
  }
  await eval_(`(async()=>{resetSceneFocus();await api('default');await setView3(false);await renderObjects();await enterFocus('face',1);fiShowTab('guide')})()`);
  const beforeImpact = (await eval_(`api('dump')`)).text;
  await eval_(`document.querySelector('#refSpecName').value='主支中線';document.querySelector('#refSpecValue').value='900';document.querySelector('#refSpecSave').click();void 0`);
  await sleep(250);
  check('P31 form opens impact preview',await eval_(`!!document.querySelector('dialog.reference-impact[open]') && !document.querySelector('#impact-confirm').disabled && document.querySelector('dialog.reference-impact').innerText.includes('500 → 900')`));
  check('P31 preview leaves world unchanged',(await eval_(`apiRequest('dump')`)).text===beforeImpact);
  await clickSelector('#impact-confirm');
  check('P31 confirm updates dependent center',await eval_(`apiRequest('references').then(r=>r.timbers.find(t=>t.id===3).geometry.centerline===900)`));
  await eval_(`window.__previewResult=api('line spec 主支中線 1200');void 0`);await sleep(100);
  await clickSelector('dialog.reference-impact .impact-actions button:first-child');
  check('P31 cancel keeps approved world',await eval_(`apiRequest('references').then(r=>r.timbers.find(t=>t.id===3).geometry.centerline===900)`));
  await eval_(`window.__previewResult=api('line spec 主支中線 0');void 0`);await sleep(100);
  check('P31 invalid impact cannot confirm',await eval_(`document.querySelector('#impact-confirm').disabled && document.querySelectorAll('.impact-violation').length>0`));
  await clickSelector('dialog.reference-impact .impact-actions button:first-child');
  await remainingShot('reference-controls');
  }
  console.log('=== P32. UI review v2: reachable panels, stable editing and complete slot workflow ===');
  const pressKey = async (key,code,vk,modifiers=0) => {
    for (const type of ['keyDown','keyUp']) await send('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:vk,modifiers});
    await sleep(150); await waitIdle();
  };
  const fillInput = async (selector,text) => {
    await clickSelector(selector);
    await pressKey('a','KeyA',65,2);
    await send('Input.insertText',{text});
  };
  await send('Emulation.setDeviceMetricsOverride',{width:1382,height:804,deviceScaleFactor:1,mobile:false});
  await setupRemaining(['boundary 1 outline 0,0 400,0 400,300 0,300','canvas-pos boundary 1 71 81']);
  const cards = await eval_(`(async()=>{
    oc.zoom=1;oc.panX=0;oc.panY=0;ocApply();
    await api('line boundary 2 outline 0,0 200,0 200,300 0,300');await renderObjects();
    return oc.faces.map(cardBox);
  })()`);
  check('M2 new card avoids offset existing bbox',cards.length===2 && (cards[0].x+cards[0].w<=cards[1].x || cards[1].x+cards[1].w<=cards[0].x || cards[0].y+cards[0].h<=cards[1].y || cards[1].y+cards[1].h<=cards[0].y),cards);
  const quick = await eval_(`[...document.querySelectorAll('.quick-create strong')].map(e=>({w:e.clientWidth,scroll:e.scrollWidth,h:e.getBoundingClientRect().height,text:e.textContent}))`);
  check('M1 library labels stay one line',quick.length===6 && quick.every(r=>r.h<=20 && r.w>=r.scroll),quick);
  const pan0=await eval_(`[oc.panX,oc.panY]`);
  await clickSelector('.object-row[data-kind="boundary"][data-id="1"]');
  check('M12 visible list selection does not pan',JSON.stringify(pan0)===JSON.stringify(await eval_(`[oc.panX,oc.panY]`)));
  check('M4 placement submit visible without scrolling',await eval_(`(()=>{const e=document.querySelector('#inspectorContent #placeSubmit'),r=e.getBoundingClientRect();return r.top>56 && r.bottom<innerHeight-32 && e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))})()`));
  check('M3 M5 M7 T3 contextual controls',await eval_(`document.querySelector('#fileMenuPop').contains(document.querySelector('#btnDatums')) && !document.querySelector('#btnScene') && document.querySelectorAll('.topbar [data-tool]').length===2 && document.querySelector('#cmdPanel').hidden`));
  await pressKey(':','Semicolon',186,8);
  check('M7 command shortcut opens focused input',await eval_(`!document.querySelector('#cmdPanel').hidden && document.activeElement.id==='cmd'`));
  await send('Input.insertText',{text:'spec 測試尺寸 123'});await pressKey('Enter','Enter',13);
  check('M7 command executes',await eval_(`api('dump').then(r=>r.text.includes('spec 測試尺寸 123'))`));
  await pressKey('Escape','Escape',27);
  check('M7 command Escape closes only command',await eval_(`document.querySelector('#cmdPanel').hidden && !oc.focus`));
  await eval_(`toast('畫布頂部驗證','ok')`);
  check('M10 toast above canvas, away from minimap',await eval_(`(()=>{const r=document.querySelector('.toast').getBoundingClientRect();return r.top>=56 && r.bottom<200})()`));
  await clickSelector('.ocard[data-id="1"] .card-enter');
  check('M8 explicit card entry',await eval_(`oc.focus?.t==='face' && oc.focus.id===1`));
  check('F1 F3 F4 four tabs, seven tools, five persistent groups',await eval_(`document.querySelectorAll('#faceInspectorTabs [data-fi-tab]').length===4 && document.querySelectorAll('#faceWorkspaceTools [data-face-tool]').length===7 && document.querySelectorAll('#faceLayerList .fl-group').length===5 && document.querySelectorAll('#faceLayerList .fl-empty').length>=3 && document.querySelector('#faceInspectorContent').contains(document.querySelector('#faceShapeButton'))`));
  await fillInput('#edgeLength0','500');await pressKey('Tab','Tab',9);await sleep(300);
  const lengthEdit = await eval_(`({focus:document.activeElement.id,a:document.querySelector('#edgeLength0').value,b:document.querySelector('#edgeLength2').value,status:document.querySelector('#status').textContent,loops:oc.bmap[1]})`);
  check('F2 real length edit retains next keyboard target',lengthEdit.focus==='edgeFixed0' && lengthEdit.a==='500' && lengthEdit.b==='500',lengthEdit);
  await eval_(`document.querySelector('#gridU').value='100 200';document.querySelector('#placeOX').value='250';document.querySelector('#faceInspectorContent').scrollTop=15;renderFaceInspector()`);
  check('F2 form drafts survive redraw',await eval_(`document.querySelector('#gridU').value==='100 200' && document.querySelector('#placeOX').value==='250'`));
  for (const width of [1382,1160,900,680,600]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:804,deviceScaleFactor:1,mobile:false});
    check('T4 workspace rows, title and tools fit @'+width,await eval_(`(()=>{const h=document.querySelector('.object-workspace-topbar').getBoundingClientRect(),s=document.querySelector('.object-workspace-statusbar').getBoundingClientRect(),t=document.querySelector('#faceWorkspaceTools').getBoundingClientRect(),a=document.querySelector('.object-workspace-actions').getBoundingClientRect(),title=document.querySelector('#workspaceTitle').getBoundingClientRect();return h.height===56 && s.height===32 && a.right<=innerWidth && t.right<=a.left+1 && title.width>0})()`));
  }
  await clickSelector('#workspaceToggleRight');
  const drawerHit=await eval_(`(()=>{const e=document.querySelector('#edgeLength0'),r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {same:e===hit,hit:hit?.outerHTML,rect:{x:r.x,y:r.y}}})()`);
  check('T2 face drawer belongs to face workspace',drawerHit.same,drawerHit);
  await remainingShot('ui-v2-mobile-face');
  await pressKey('Escape','Escape',27);
  check('T2 drawer Escape retains workspace',await eval_(`oc.focus?.t==='face' && !document.body.classList.contains('drawer-right-open') && document.activeElement.id==='workspaceToggleRight'`));
  await clickSelector('#workspaceToggleLeft');
  check('T2 face layer drawer hit target',await eval_(`(()=>{const e=document.querySelector('#faceLayerList .fl-empty'),r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))})()`));
  await clickSelector('#workspaceBackButton');
  await clickSelector('#toggleLeft');
  check('T2 main drawer exposes creation',await eval_(`(()=>{const e=document.querySelector('#btnBox6'),r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))})()`));
  await pressKey('Escape','Escape',27);

  await setupRemaining(['space 1']);await eval_(`enterFocus('space',1)`);
  await clickSelector('#workspaceToggleRight');
  check('S1 empty space exposes all six actions',await eval_(`document.querySelectorAll('#spaceInspectorContent .slot-empty').length===6`));
  await clickSelector('[data-slot-label="地板"]');
  check('S1 empty slot starts visible guided creation',await eval_(`!oc.focus && oc.drawTool==='rect' && pendingSlot?.space===1 && !document.querySelector('#canvasModeHint').hidden`));
  await drag(330,430,510,600);await sleep(450);await waitIdle();
  const slotDrawn=await eval_(`({focus:oc.focus,pending:pendingSlot,u:document.querySelector('#faceInspectorContent #placeU')?.value,v:document.querySelector('#faceInspectorContent #placeV')?.value,status:document.querySelector('#status').textContent})`);
  check('S1 drawn face continues into intended placement',slotDrawn.focus?.t==='face' && slotDrawn.pending?.bid===slotDrawn.focus.id && slotDrawn.u==='+y' && slotDrawn.v==='+x',slotDrawn);
  await fillInput('#edgeLength0','800');await pressKey('Tab','Tab',9);await sleep(200);
  await fillInput('#edgeLength1','600');await pressKey('Tab','Tab',9);await sleep(200);
  await clickSelector('#faceInspectorContent #placeSubmit');await sleep(500);
  const slotPlaced=await eval_(`api('objects').then(r=>({focus:oc.focus,faces:r.faces,spaces:r.spaces,status:document.querySelector('#status').textContent}))`);
  check('S1 explicit placement returns to original space',slotPlaced.focus?.t==='space' && slotPlaced.focus.id===1 && slotPlaced.faces.length===1 && slotPlaced.faces[0].placed && slotPlaced.spaces[0].members.includes(slotPlaced.faces[0].id),slotPlaced);
  await pressKey('z','KeyZ',90,2);await sleep(300);
  check('S1 placement and membership undo together',await eval_(`api('objects').then(r=>r.faces.length===1 && !r.faces[0].placed && r.spaces[0].members.length===0)`));
  await clickSelector('#workspaceToggleRight');await clickSelector('[data-slot-label="地板"]');
  await clickSelector('#faceInspectorContent [data-place-preset="天花"]');
  const slotDirection=await eval_(`({pending:pendingSlot,focus:oc.focus,u:document.querySelector('#faceInspectorContent #placeU').value,v:document.querySelector('#faceInspectorContent #placeV').value,disabled:document.querySelector('#faceInspectorContent #placeSubmit').disabled,valid:document.querySelector('#faceInspectorContent #placeValid').textContent})`);
  check('S1 changed orientation cannot silently fill wrong slot',slotDirection.disabled,slotDirection);
  await pressKey('Escape','Escape',27);await clickSelector('#workspaceBackButton');

  await send('Emulation.setDeviceMetricsOverride',{width:1382,height:804,deviceScaleFactor:1,mobile:false});
  await setupRemaining(['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000','space 1 boundary 1']);
  await eval_(`enterFocus('face',1)`);await clickSelector('[data-fi-tab="timber"]');
  await fillInput('#tbA','35');await clickSelector('#tbPlace');
  check('F5 timber settings activate placement with matching hint',await eval_(`fe.tool==='timber' && document.activeElement.id==='faceEditorViewport' && document.querySelector('#faceCanvasHint').textContent.includes('35')`));
  await clickSelector('[data-fi-tab="prop"]');
  await clickSelector('#placeDetails summary');await clickSelector('#projToggle');
  await eval_(`renderFaceInspector()`);
  check('F9 both disclosures keep expanded state',await eval_(`document.querySelector('#placeDetails').open && document.querySelector('#projectionDetails').open`));
  await clickSelector('#workspaceBackButton');await clickSelector('#btnObj');
  check('V1 V2 toolbar does not overlap drawing and empty inspector collapses',await eval_(`(()=>{const t=document.querySelector('#viewToolbar').getBoundingClientRect(),c=document.querySelector('#cv').getBoundingClientRect(),r=document.querySelector('.sidebar-right').getBoundingClientRect();return c.top>=t.bottom-1 && c.height>400 && r.width===0})()`));
  await clickSelector('#btnObj');
  check('V3 selecting three-view twice stays in three-view',await eval_(`!oc.on && [...document.querySelectorAll('.topbar [data-tool]')].every(b=>b.disabled)`));
  await remainingShot('ui-v2-three-view');
  await clickSelector('#btnCanvasView');
  check('V3 canvas switch restores active main tools',await eval_(`oc.on && [...document.querySelectorAll('.topbar [data-tool]')].every(b=>!b.disabled)`));

  /* ================= P33. 主畫布 boundary 檢視器:外環邊 · 尺寸確認清單(RC-POLYGON-PLAN §5.A.1.10,🔒 Q16) =================
   * P21/P23 編號已被既有段落占用,依 §5.A.1.14 規則往後遞補用 P33。
   * 涵蓋:清單存在且列數=外環邊數、每列顯示長度 mm 與 F/X 狀態、改長度/切 F/X 後世界對應改變、
   * 非法長度(0/負/非數字)被拒且世界不變、面內右欄清單與主畫布清單對同一 boundary 顯示一致。 */
  console.log('=== P33. 主畫布外環邊 · 尺寸確認清單(§5.A.1.10) ===');
  const readMainEdgeList = () => eval_(`(()=>{
    const pane = document.querySelector('#inspectorContent');
    const rows = [...pane.querySelectorAll('.edge-row')];
    return {
      n: rows.length,
      title: pane.textContent.includes('外環邊 · 尺寸確認'),
      lens: rows.map((_,i)=>document.querySelector('#mainEdgeLength'+i)?.value),
      fx: rows.map((_,i)=>({
        f: document.querySelector('#mainEdgeFixed'+i)?.classList.contains('on'),
        x: document.querySelector('#mainEdgeFree'+i)?.classList.contains('on')
      }))
    };
  })()`);
  const readFaceEdgeList = () => eval_(`(()=>{
    const pane = document.querySelector('#faceInspectorContent');
    const rows = [...pane.querySelectorAll('.edge-row')];
    return {
      n: rows.length,
      lens: rows.map((_,i)=>document.querySelector('#edgeLength'+i)?.value),
      fx: rows.map((_,i)=>({
        f: document.querySelector('#edgeFixed'+i)?.classList.contains('on'),
        x: document.querySelector('#edgeFree'+i)?.classList.contains('on')
      }))
    };
  })()`);
  const readBoundary1 = () => eval_(`api('boundary 1').then(b=>JSON.stringify(b.loops))`);

  await setupRemaining(['boundary 1 outline 0,0 400,0 400,300 0,300','canvas-pos boundary 1 60 60']);
  await eval_(`selectObject('boundary',1)`); await sleep(300);
  const mainList0 = await readMainEdgeList();
  check('P33-1 主畫布清單存在且列數=外環邊數', mainList0.n===4 && mainList0.title, mainList0);
  check('P33-2 每列顯示長度mm與F/X狀態(預設全F)', JSON.stringify(mainList0.lens)===JSON.stringify(['400','300','400','300']) &&
    mainList0.fx.every(v=>v.f && !v.x), mainList0);

  /* 改長度 → outline 座標對應改變(邊0 400→500,寬跟著變,高不變) */
  await fillInput('#mainEdgeLength0','500'); await pressKey('Tab','Tab',9); await sleep(300);
  const lenChanged = await eval_(`api('boundary 1').then(b=>{
    const vs=b.loops[0].verts;
    return {w: vs[1][0]-vs[0][0], h: vs[2][1]-vs[1][1]};
  })`);
  check('P33-3 改長度後 outline 座標對應改變', lenChanged.w===500 && lenChanged.h===300, lenChanged);

  /* 切 F/X → fixity 對應改變,再切回驗證雙向 */
  await clickSelector('#mainEdgeFree1');
  const fixChanged = await eval_(`api('boundary 1').then(b=>b.loops[0].fixity[1])`);
  check('P33-4 切X後 fixity 對應改變', fixChanged===0, fixChanged);
  await clickSelector('#mainEdgeFixed1');
  const fixRestored = await eval_(`api('boundary 1').then(b=>b.loops[0].fixity[1])`);
  check('P33-5 切回F fixity 還原', fixRestored===1, fixRestored);

  /* 非法長度:0、負、非數字 → 拒絕且世界不變 */
  const beforeIllegal = await readBoundary1();
  await fillInput('#mainEdgeLength0','0'); await pressKey('Tab','Tab',9); await sleep(300);
  const afterZero = await readBoundary1();
  check('P33-6 長度0被拒且世界不變', afterZero===beforeIllegal, {before:beforeIllegal,after:afterZero});
  await fillInput('#mainEdgeLength0','-50'); await pressKey('Tab','Tab',9); await sleep(300);
  const afterNeg = await readBoundary1();
  check('P33-7 負長度被拒且世界不變', afterNeg===beforeIllegal, {before:beforeIllegal,after:afterNeg});
  const nanResult = await eval_(`commitEdgeLength(1, oc.bmap[1], 0, NaN)`);
  const afterNaN = await readBoundary1();
  check('P33-8 非數字長度被拒且世界不變', nanResult===false && afterNaN===beforeIllegal,
    {nanResult,before:beforeIllegal,after:afterNaN});

  /* 面內工作區右欄清單與主畫布清單對同一 boundary 顯示一致 */
  await eval_(`enterFocus('face',1)`); await sleep(300);
  const feList = await readFaceEdgeList();
  await eval_(`leaveFocus()`); await sleep(200);
  await eval_(`selectObject('boundary',1)`); await sleep(300);
  const mainList2 = await readMainEdgeList();
  check('P33-9 面內與主畫布清單對同一boundary顯示一致',
    feList.n===mainList2.n && JSON.stringify(feList.lens)===JSON.stringify(mainList2.lens) &&
    JSON.stringify(feList.fx)===JSON.stringify(mainList2.fx), {feList,mainList2});

  /* ================= P34. P 鍵/「＋面·多邊形」:建面卡→面內畫外環(GEO-186 b) =================
   * 2026-09-24 GEO-186(b) 拍板:主畫布不再用 mm 畫多邊形——同一張畫布混用
   * 「mm 繪圖」與「固定 200×156 卡片排版」兩套座標是 GEO-186 的根因
   * (畫 4000×3000 的房間要縮到 2–5%,閉合後卡片被放到多邊形左上角、
   * 縮成一個點——GEO-187「找不到卡片」)。新流程:
   *   P/「＋面·多邊形」= 建預設外環的面卡 → 自動進入面內工作區並啟用「重畫外環」
   *   → 面內以實際 mm 逐點畫 → Esc 回畫布。
   * 畫布端逐點閉合機制(吸附/補角/Esc 階梯/鍵入長度/草稿層)已隨畫布繪圖移除;
   * PolyDraft 狀態機行為由 polydraft_test.js 單元測試 + 面內 §P35/P36 繼續覆蓋。 */
  console.log('=== P34. P=建面卡→面內畫外環(GEO-186) ===');
  const ocOrigin = async () => eval_(`(()=>{const r=document.getElementById('ocv').getBoundingClientRect();
    return {x:r.left,y:r.top};})()`);
  /* setupRemaining([]) 重置成完全空世界後,#emptyState(「建立第一個領域物件」提示卡)
     會蓋在畫布正中央(.empty-illustration 有 pointer-events:auto,120×80px 置中),
     建出新物件、drawObjects() 重繪之前都不會自動收起——點擊若剛好落在置中那塊區域
     會被這張卡片吃掉,不會傳到 #ocv。這裡直接把它隱藏,建出新面後 drawObjects()
     會依當下物件數自行重算 hidden,不需要手動復原。 */
  const emptyWorld = async () => {
    await setupRemaining([]);
    await eval_(`document.getElementById('emptyState').hidden = true`);
  };

  /* 按 P → 面數+1、預設外環佔位、自動進入面內工作區且重畫外環就緒、新面被選取 */
  await emptyWorld();
  await eval_(`oc.zoom=1;oc.panX=0;oc.panY=0;ocApply()`);
  const p34f0 = await eval_(`api('objects').then(r=>r.faces.length)`);
  await pressKey('p','KeyP',80);
  await sleep(900);
  const t1 = await eval_(`(async()=>{
    const r = await api('objects');
    const f = r.faces[r.faces.length-1];
    const b = await api('boundary '+f.id);
    return {faces:r.faces.length, id:f.id, verts:b.loops[0].verts,
      focus:oc.focus, tool:fe.tool, sel:oc.sel,
      st:document.getElementById('status').textContent};})()`);
  check('P34-1 按 P 建面卡:面數+1、自動進入面內工作區、重畫外環就緒、新面被選取',
    t1.faces===p34f0+1 && t1.focus && t1.focus.t==='face' && t1.focus.id===t1.id &&
    t1.tool==='redraw' && t1.sel && t1.sel.id===t1.id, t1);
  check('P34-1b 狀態列提示「逐點畫出外環」與 Esc 返回', /逐點畫出外環/.test(t1.st) && /Esc/.test(t1.st), t1.st);
  check('P34-2 預設外環是 4000×3000 矩形佔位(進面內後被 redraw 整份取代)',
    JSON.stringify(t1.verts)==='[[0,0],[4000,0],[4000,3000],[0,3000]]', t1.verts);

  /* 面內以實際 mm 畫 L 形外環:固定 fe.zoom=1/pan=0 讓螢幕像素=面內 mm;
     落點全取 50 的倍數,與面內格距(feGridStep()=25、feSnap()=50)都對齊,
     吸附開著也不偏移。末點(100,700)與起點(100,100)同軸,不需補角,6 點閉合即 L。 */
  const f34 = t1.id;
  await eval_(`fe.zoom=1;fe.panX=0;fe.panY=0;feApply();
    document.getElementById('faceSnapToggle').checked = true`);
  const fo34 = await eval_(`(()=>{const r=document.getElementById('faceEditorSvg').getBoundingClientRect();
    return {x:r.left,y:r.top};})()`);
  for (const [x, y] of [[100,100],[700,100],[700,400],[400,400],[400,700],[100,700]]) {
    await click(fo34.x+x, fo34.y+y); await sleep(90);
  }
  await click(fo34.x+100, fo34.y+100); await sleep(900);   /* 點回起點閉合 */
  const drawn34 = await eval_(`api('boundary '+${f34}).then(b=>JSON.stringify(b.loops[0].verts))`);
  check('P34-3 面內 redraw 以實際 mm 畫外環,點回起點閉合後世界 outline 更新',
    drawn34==='[[100,100],[700,100],[700,400],[400,400],[400,700],[100,700]]', drawn34);

  /* Esc 回畫布:卡片可見且在視野內(落點是建立當下的視野中心)、維持選取 */
  await pressKey('Escape','Escape',27); await sleep(500);
  const back34 = await eval_(`(()=>{const c=document.querySelector('.ocard[data-id="${f34}"]');
    const v=document.getElementById('ocv').getBoundingClientRect();
    const r=c&&c.getBoundingClientRect();
    return {focus:oc.focus, sel:oc.sel, card:!!r,
      inView:!!r && r.left>=v.left && r.right<=v.right && r.top>=v.top && r.bottom<=v.bottom};})()`);
  check('P34-4 Esc 回畫布:卡片可見、在視野內、維持選取',
    !back34.focus && back34.card && back34.inView && back34.sel && back34.sel.id===f34, back34);

  /* pendingSlot:空間槽位「＋放置」會備妥矩形工具;此時按 P 改走建面卡路徑,
     新面仍自動帶入該槽位、進面內直接開「放置」頁(S1 矩形路徑的對應分支) */
  await setupRemaining(['space 1']);
  await eval_(`enterFocus('space',1)`); await sleep(400);
  await eval_(`document.querySelector('#spaceInspectorContent .slot-empty').click()`); await sleep(400);
  const armed34 = await eval_(`({focus:oc.focus, drawTool:oc.drawTool,
    slot:pendingSlot && {space:pendingSlot.space, preset:pendingSlot.presetName}})`);
  await pressKey('p','KeyP',80); await sleep(900);
  const slotFlow = await eval_(`({focus:oc.focus, bid:pendingSlot && pendingSlot.bid,
    tab:(document.querySelector('#faceInspectorTabs [data-fi-tab].active')||{}).dataset?.fiTab})`);
  check('P34-5 槽位「＋放置」後按 P:新面帶入 pendingSlot、面內工作區直接開放置頁',
    !armed34.focus && armed34.drawTool==='rect' && armed34.slot && armed34.slot.space===1 &&
    slotFlow.focus && slotFlow.focus.t==='face' && slotFlow.bid===slotFlow.focus.id &&
    slotFlow.tab==='prop', {armed34, slotFlow});
  await eval_(`leaveFocus()`); await sleep(400);


  /* ================= P35. 面內「重畫外環」逐點閉合改接共用 PolyDraft(diff#12 面內段) =================
   * RC-POLYGON-PLAN.md §5.A.1.12/.16、POLYDRAFT-API.md §6。續 §P34 之後編號。
   * 全程固定 fe.zoom=1/panX=0/panY=0，讓螢幕像素座標與面 uv mm 座標 1:1 對應。
   * polydraft.js 本體不受本節影響(該模組由另一 agent 同時維護 tryClose 收尾驗證，本節只讀)。 */
  console.log('=== P35. 面內重畫外環逐點閉合(polydraft,diff#12 面內段) ===');
  const feOrigin = async () => eval_(`(()=>{const r=document.getElementById('faceEditorSvg').getBoundingClientRect();
    return {x:r.left,y:r.top};})()`);
  /* 每次都用一個夠大的外環(4000×3000)進場：重畫是整份重建 loops[0]，舊外環正被取代
     不算「既有」(POLYDRAFT-API.md §6)，這裡只是給新草稿足夠的畫布空間，座標互不干擾。 */
  const enterFaceRedraw = async () => {
    await setupRemaining(['boundary 1 outline 0,0 4000,0 4000,3000 0,3000']);
    await eval_(`(async()=>{ await enterFocus('face', 1);
      fe.zoom = 1; fe.panX = 0; fe.panY = 0; feApply(); })()`);
    await sleep(250);
  };

  /* diff#12:進入面內按 e 後草稿層存在 */
  await enterFaceRedraw();
  await pressKey('e', 'KeyE', 69);
  const t35_1 = await eval_(`({tool: fe.tool, layer: !!document.getElementById('feDraftLayer')})`);
  check('P35-1 面內按 e 後 fe.tool=redraw 且 #feDraftLayer 草稿層存在',
    t35_1.tool === 'redraw' && t35_1.layer, t35_1);

  /* diff#3/§5.A.1.3:面內 gridMm 不是固定 250，是 feGridStep()(B4 依 zoom 挑距)算出來的值，
     測試自己讀取這個值再驗證吸附後座標是它的整數倍——snapOn 預設開(#faceSnapToggle checked)。 */
  const fo2 = await feOrigin();
  const gridStep2 = await eval_(`feGridStep()`);
  await click(fo2.x + 13, fo2.y + 8);
  await sleep(150);
  const fsnap2 = await eval_(`fe.draft.pts[0]`);
  check(`P35-2 點擊吸附到 B4 格距(zoom=1→${gridStep2}mm)`,
    fsnap2[0] % gridStep2 === 0 && fsnap2[1] % gridStep2 === 0, { fsnap2, gridStep2 });

  /* diff#6:靠近既有「非相鄰」頂點 ±8px 出現對齊參考線並吸附該軸(同 P34-7 手法，
     驗證面內也有這道吸附——關 snapOn 避免格線吸附干擾像素級判斷，用完即還原)。 */
  await enterFaceRedraw();
  await eval_(`feSetTool('redraw'); document.getElementById('faceSnapToggle').checked = false`);
  const fo3 = await feOrigin();
  await click(fo3.x + 100, fo3.y + 100); await sleep(90);
  await click(fo3.x + 500, fo3.y + 100); await sleep(90);
  await click(fo3.x + 500, fo3.y + 400); await sleep(90);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: fo3.x + 103, y: fo3.y + 600 });
  await sleep(150);
  const guide3 = await eval_(`({guides: fe.draftPreview.guides, cur: fe.draftPreview.cur,
    lines: document.querySelectorAll('#feDraftLayer .draft-align-guide').length})`);
  check('P35-3 靠近既有頂點±8px 吸附該軸並畫參考線(對齊起點 x=100)',
    guide3.lines > 0 && guide3.cur[0] === 100 &&
    guide3.guides.some(g => g.axis === 'x' && g.value === 100), guide3);

  /* diff#7/#9:末點與起點不同軸 → 自動補一個直角轉折，dump 頂點數 = 點擊數 3 + 1(同 P34-9) */
  await enterFaceRedraw();
  await eval_(`feSetTool('redraw')`);
  const fo4 = await feOrigin();
  await click(fo4.x + 100, fo4.y + 100); await sleep(90);
  await click(fo4.x + 400, fo4.y + 100); await sleep(90);
  await click(fo4.x + 400, fo4.y + 400); await sleep(90);
  await pressKey('Enter', 'Enter', 13); await sleep(700);
  const closed4 = await eval_(`api('boundary 1').then(b => b.loops[0].verts)`);
  /* 不只驗頂點數(舊碼點 3 下因未達 4 點而拒絕、boundary 維持原狀，巧合也是 4 頂點但內容是
     沒被取代的原始 4000×3000 外環)——這裡逐點驗證真的是新畫的 L 轉角形狀，
     [400,400] 之後補上 [100,400] 這個直角轉折點，不是舊外環殘留。 */
  check('P35-4 末點不同軸自動補直角(dump 頂點數=點擊數 3 + 1，且內容確實是新外環)',
    JSON.stringify(closed4) === JSON.stringify([[100,100],[400,100],[400,400],[100,400]]), closed4);

  /* diff#8:與自身既有邊交叉時橡皮筋轉紅、點擊無效、世界不變。
     existingEdges 含自身邊的證明:feDraftOpts() 恆傳 existingEdges:[]（重畫外環沒有
     「既有」邊可比，見上方 enterFaceRedraw 的說明），CROSS 仍被抓到，證明是
     PolyDraft.place 內部對 state.pts(草稿自身已定邊)自動比對的結果，不靠 existingEdges
     陣列本身——與主畫布 P34-10a/b(同樣傳 existingEdges:[])是同一套機制，共用的直接證據。 */
  await enterFaceRedraw();
  await eval_(`feSetTool('redraw')`);
  const fo5 = await feOrigin();
  await click(fo5.x + 100, fo5.y + 100); await sleep(90);
  await click(fo5.x + 100, fo5.y + 500); await sleep(90);
  await click(fo5.x + 500, fo5.y + 500); await sleep(90);
  await click(fo5.x + 500, fo5.y + 200); await sleep(90);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: fo5.x + 50, y: fo5.y + 200 });
  await sleep(150);
  const cross5 = await eval_(`({error: fe.draftPreview.error,
    rubberError: !!document.querySelector('#feDraftLayer .draft-rubber.error')})`);
  check('P35-5a 面內與自身既有邊交叉時橡皮筋轉紅(CROSS)',
    cross5.error && cross5.error.code === 'CROSS' && cross5.rubberError, cross5);
  const beforeCrossPts = await eval_(`fe.draft.pts.length`);
  await click(fo5.x + 50, fo5.y + 200); await sleep(150);
  const afterCrossPts = await eval_(`fe.draft.pts.length`);
  const worldUnchanged5 = await eval_(`api('boundary 1').then(b => b.loops[0].verts.length)`);
  check('P35-5b 交叉時點擊無效(頂點數不變)、世界不變',
    afterCrossPts === beforeCrossPts && worldUnchanged5 === 4,
    { beforeCrossPts, afterCrossPts, worldUnchanged5 });

  /* diff#7:Enter 閉合與點回起點閉合，同一組點擊序列結果一致(同 P34-8 手法的子集，
     面內沒有雙擊閉合，兩種既夠) */
  const drawFaceRect = async () => {
    await enterFaceRedraw();
    await eval_(`feSetTool('redraw')`);
    const o = await feOrigin();
    await click(o.x + 100, o.y + 100); await sleep(90);
    await click(o.x + 500, o.y + 100); await sleep(90);
    await click(o.x + 500, o.y + 400); await sleep(90);
    await click(o.x + 100, o.y + 400); await sleep(90);
    return o;
  };
  let ofa = await drawFaceRect();
  await click(ofa.x + 100, ofa.y + 100); await sleep(700);
  const closeFA = await eval_(`api('boundary 1').then(b => JSON.stringify(b.loops[0].verts))`);
  ofa = await drawFaceRect();
  await pressKey('Enter', 'Enter', 13); await sleep(700);
  const closeFB = await eval_(`api('boundary 1').then(b => JSON.stringify(b.loops[0].verts))`);
  check('P35-6 Enter 閉合與點回起點閉合結果相同', closeFA === closeFB, { closeFA, closeFB });

  /* UIUX-FIX-PLAN「Esc 三段式決定 🔒」既有七階梯不變——驗其中三級的順序：
     清鍵入長度(第4級) → 清草稿並提示「再按」(第6級) → 離開工作區(第7級)。 */
  await enterFaceRedraw();
  await eval_(`feSetTool('redraw')`);
  const fo7 = await feOrigin();
  await click(fo7.x + 100, fo7.y + 100); await sleep(90);
  await click(fo7.x + 300, fo7.y + 100); await sleep(90);
  await pressKey('4', 'Digit4', 52); await pressKey('2', 'Digit2', 50);
  const typed7 = await eval_(`fe.lenBuf`);
  check('P35-7a 面內鍵入長度中 fe.lenBuf 非空', typed7 === '42', typed7);
  await pressKey('Escape', 'Escape', 27); await sleep(150);
  const esc7a = await eval_(`({lenBuf: fe.lenBuf, drag: !!fe.drag, focus: !!oc.focus})`);
  check('P35-7b 第一次 Esc(第4級)只清鍵入長度，草稿與工作區不變',
    esc7a.lenBuf === '' && esc7a.drag && esc7a.focus, esc7a);
  await pressKey('Escape', 'Escape', 27); await sleep(150);
  const esc7b = await eval_(`({drag: !!fe.drag, focus: !!oc.focus,
    toast: [...document.querySelectorAll('#toastRegion .toast')].map(t => t.textContent).join('|')})`);
  check('P35-7c 第二次 Esc(第6級)清草稿並提示「再按」，仍在工作區',
    !esc7b.drag && esc7b.focus && esc7b.toast.includes('再按'), esc7b);
  await pressKey('Escape', 'Escape', 27); await sleep(300);
  const esc7c = await eval_(`!!oc.focus`);
  check('P35-7d 第三次 Esc(第7級)離開工作區', esc7c === false, esc7c);

  /* diff#10/§5.A.1.10(既有共用邏輯):閉合後面內右欄「外環邊 · 尺寸確認」清單列數=新邊數 */
  ofa = await drawFaceRect();
  await click(ofa.x + 100, ofa.y + 100); await sleep(700);
  const feList8 = await readFaceEdgeList();
  check('P35-8 閉合後面內右欄「外環邊 · 尺寸確認」清單列數=新邊數', feList8.n === 4, feList8);

  /* 原 P35-9(主畫布 P 與面內 e 對同序列產生相同 outline、覆蓋兩側格距刻意分歧)已移除:
     GEO-186(b) 後主畫布不再有 mm 繪圖工具,「兩個呼叫點共用 PolyDraft」只剩面內一側,
     對照失去意義;PolyDraft 狀態機行為由 polydraft_test.js 單元測試覆蓋。 */

  /* ================= P36. 對抗審查「多邊形逐點閉合」UI 接線 finding =================
   * 原 4 個 finding 中 finding-1(oc.polyDraft 重置)/finding-2(undo 後草稿層閃空)/
   * finding-3 主畫布段都是畫布 poly 機器的接線修正——GEO-186(b) 機器移除後一併移除。
   * 保留 finding-3 的面內段:鍵入長度錯誤的持久回饋(狀態列+紅橡皮筋)。 */
  console.log('=== P36. 對抗審查 finding 修正(面內段) ===');

  /* finding-3 面內段:「C 形」座標(P35-5a 同款)鍵入長度 450 觸發 CROSS——
     面內沒有 .hint-context 容器(只有主畫布 #canvasModeHint 有這個結構)，
     改驗狀態列 + 紅橡皮筋兩項持久回饋。 */
  await enterFaceRedraw();
  await eval_(`feSetTool('redraw'); document.getElementById('faceSnapToggle').checked = false`);
  const fo36 = await feOrigin();
  await click(fo36.x+100, fo36.y+100); await sleep(90);
  await click(fo36.x+100, fo36.y+500); await sleep(90);
  await click(fo36.x+500, fo36.y+500); await sleep(90);
  await click(fo36.x+500, fo36.y+200); await sleep(90);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: fo36.x+50, y: fo36.y+200 });
  await sleep(150);
  await pressKey('4','Digit4',52); await pressKey('5','Digit5',53); await pressKey('0','Digit0',48);
  await pressKey('Enter','Enter',13); await sleep(150);
  const t3b = await eval_(`({
    statusText: document.getElementById('status').textContent.replace('✗','[X]'),
    rubberError: !!document.querySelector('#feDraftLayer .draft-rubber.error'),
    typed: fe.draft.typed, ptsLen: fe.draft.pts.length
  })`);
  check('P36-3b 面內鍵入會交叉的長度後 Enter,狀態列顯示警示文字、橡皮筋轉紅(面內沒有 .hint-context,狀態列+紅橡皮筋是對應的持久回饋;不再只有一次性 toast)',
    /交叉/.test(t3b.statusText) && t3b.rubberError && t3b.typed==='450' && t3b.ptsLen===4, t3b);

  await pressKey('Escape','Escape',27); await sleep(150);
  const t3b2 = await eval_(`({
    rubberError: !!document.querySelector('#feDraftLayer .draft-rubber.error'),
    typed: fe.lenBuf
  })`);
  check('P36-3b2 面內清數字(Esc 第一階)後鍵入長度錯誤態消失(橡皮筋不再紅)',
    t3b2.typed==='' && !t3b2.rubberError, t3b2);
  await eval_(`document.getElementById('faceSnapToggle').checked = true; leaveFocus()`);  /* 還原頁面預設 */

  console.log('=== P37. 工作區狀態與手機操作回歸 ===');
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
  await setupRemaining(['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000']);
  await eval_(`enterFocus('face',1)`);
  await clickSelector('#placeDetails > summary');
  await fillInput('#faceInspectorContent #placeOZ','3000');
  await clickSelector('#faceInspectorContent #placeSubmit');
  check('P37 placement update refreshes header',await eval_(`document.querySelector('#workspacePlaceTag').textContent.includes('3000')`));
  await clickSelector('#faceUndoButton');
  check('P37 placement undo refreshes form and header',await eval_(`document.querySelector('#faceInspectorContent #placeOZ').value==='2500' && document.querySelector('#workspacePlaceTag').textContent.includes('2500')`));
  await clickSelector('#faceRedoButton');
  check('P37 placement redo refreshes form and header',await eval_(`document.querySelector('#faceInspectorContent #placeOZ').value==='3000' && document.querySelector('#workspacePlaceTag').textContent.includes('3000')`));
  if (!await eval_(`document.querySelector('#placeDetails').open`)) await clickSelector('#placeDetails > summary');
  await fillInput('#faceInspectorContent #placeOZ','3100');
  await eval_(`feAfterChange()`);
  check('P37 inspector rebuild preserves unsubmitted placement draft and focus',await eval_(`document.querySelector('#faceInspectorContent #placeOZ').value==='3100' && document.activeElement.id==='placeOZ' && feSurf(1).origin[2]===3000`));

  /* Pause the second boundary response, leaving the existing face SVG interactive.
     This exercises the actual refresh and pointer handlers, not a copied cache model. */
  await setupRemaining([
    'boundary 1 outline 0,0 4000,0 4000,3000 0,3000',
    'boundary 2 outline 0,0 4000,0 4000,3000 0,3000'
  ]);
  await eval_(`enterFocus('face',2)`);
  const p37Exceptions=excN;
  await eval_(`(()=>{
    const original=api, oldCache=oc.bmap;
    const gate={original,oldCache,waiting:false,blocked:false};
    window.__p37BoundaryGate=gate;
    api=async function(cmd){
      if(cmd==='boundary 2' && !gate.blocked){
        gate.blocked=true;gate.waiting=true;
        await new Promise(resolve=>{gate.release=resolve});
      }
      return original(cmd);
    };
    gate.refresh=renderObjects();
  })()`);
  try {
    let pendingBoundary=false;
    for(let i=0;i<100;i++) {
      pendingBoundary=await eval_(`window.__p37BoundaryGate.waiting`);
      if(pendingBoundary) break;
      await sleep(25);
    }
    const cache=await eval_(`({same:oc.bmap===window.__p37BoundaryGate.oldCache,ids:Object.keys(oc.bmap),focus:oc.focus?.id})`);
    check('P37 pending multi-face refresh retains complete published cache',pendingBoundary && cache.same && cache.ids.includes('1') && cache.ids.includes('2') && cache.focus===2,cache);
    await clickSelector('#faceEditorRoot [data-face-hit="e:0:0"]');
    check('P37 existing face edge remains interactive while boundary refresh waits',excN===p37Exceptions && await eval_(`oc.focus?.id===2 && !!oc.bmap[2] && !document.querySelector('#objectWorkspace').hidden`));
  } finally {
    await eval_(`(async()=>{
      const gate=window.__p37BoundaryGate;
      api=gate.original;
      if(gate.release)gate.release();
      await gate.refresh;
      delete window.__p37BoundaryGate;
    })()`);
  }

  for (const kind of ['face','space']) {
    await setupRemaining(kind==='face' ? ['boundary 1 outline 0,0 4000,0 4000,3000 0,3000'] : ['space 1']);
    await eval_(`enterFocus('${kind}',1)`);
    await clickSelector('#faceUndoButton');
    const gone=await eval_(`({focus:oc.focus,edit:oc.edit,hidden:document.querySelector('#objectWorkspace').hidden,svg:document.querySelector('#faceEditorRoot').childElementCount})`);
    check('P37 undo removes focused '+kind+' and clears workspace',!gone.focus && !gone.edit && gone.hidden && gone.svg===0,gone);
  }

  for (const width of [390,320]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:804,deviceScaleFactor:1,mobile:false});
    await eval_(`closePanels();closeMenus()`);await sleep(200);
    const buttons=await eval_(`[...document.querySelectorAll('.topbar button')].filter(e=>e.getClientRects().length && getComputedStyle(e).visibility!=='hidden').map(e=>{const r=e.getBoundingClientRect();return {id:e.id,inside:r.left>=0 && r.right<=innerWidth && r.top>=0 && r.bottom<=innerHeight,hit:e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}})`);
    check('P37 all visible topbar buttons fit and are reachable @'+width,buttons.length>0 && buttons.every(b=>b.inside && b.hit),buttons);
    if (width===390) await eval_(`showCommand(true)`);
    await clickSelector('#toggleLeft');
    await clickSelector('#searchInput');
    await pressKey('Escape','Escape',27);
    check('P37 search Escape closes drawer and restores toggle @'+width,await eval_(`!document.body.classList.contains('drawer-left-open') && document.activeElement.id==='toggleLeft'`));
    if (width===390) {
      check('P37 search Escape leaves background command panel open',await eval_(`!document.querySelector('#cmdPanel').hidden`));
      await eval_(`showCommand(false)`);
    }
  }
  await send('Emulation.setDeviceMetricsOverride',{width:600,height:804,deviceScaleFactor:1,mobile:false});
  for (const [button,dialog,field,cancel] of [
    ['#btnBox6','#box6Dialog','#box6W','#box6Cancel'],
    ['#btnNewColumn','#rcDialog','#rcW','#rcCancel']
  ]) {
    await clickSelector('#toggleLeft');
    await clickSelector(button);
    await clickSelector(field);
    check('P37 drawer closes before opening '+dialog,await eval_(`!document.body.classList.contains('drawer-left-open') && !document.querySelector('${dialog}').hidden && document.activeElement.id==='${field.slice(1)}'`));
    await clickSelector(cancel);
  }

  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
  /* geometry-core/transactions.inc::reference_default_world defines spec 主支中線 500,
     guide 1 and dependent timber 3, so editing it must open an impact preview. */
  await eval_(`(async()=>{resetSceneFocus();await api('default');await renderObjects();await enterFocus('face',1)})()`);
  await clickSelector('[data-fi-tab="guide"]');
  const p37Before=(await eval_(`apiRequest('dump')`)).text;
  await fillInput('#refSpecName','主支中線');
  await fillInput('#refSpecValue','900');
  await clickSelector('#refSpecSave');
  check('P37 reference form opens native impact dialog',await eval_(`!!document.querySelector('dialog.reference-impact[open]')`));
  await pressKey('Escape','Escape',27);
  check('P37 impact Escape cancels only dialog and retains face',await eval_(`!document.querySelector('dialog.reference-impact[open]') && oc.focus?.t==='face' && oc.focus.id===1 && !document.querySelector('#objectWorkspace').hidden`));
  check('P37 impact Escape leaves model unchanged',(await eval_(`apiRequest('dump')`)).text===p37Before);
  check('P30 no uncaught browser exceptions',excN===0,excN);

  console.log('=== P38. 回報收件匣(GEO-183):F8 面板、Esc 不外洩、指出位置不觸發 app、送出寫檔、程式錯誤自動擷取 ===');
  const fbDir = process.env.GEOMETRY_FEEDBACK_DIR;
  const fbList = () => fbDir && require('fs').existsSync(fbDir)
    ? require('fs').readdirSync(fbDir).filter(n => n.startsWith('F-')).sort() : [];
  const fbMeta = id => JSON.parse(require('fs').readFileSync(require('path').join(fbDir, id, 'meta.json'), 'utf8'));
  await send('Emulation.setDeviceMetricsOverride',{width:1382,height:900,deviceScaleFactor:1,mobile:false});
  await eval_(`(async()=>{resetSceneFocus();await api('default');await renderObjects();await enterFocus('face',1)})()`);
  await eval_(`api('line place 999 on 1 at-line guide 1')`);
  check('P38 黑盒子記下被拒的指令與錯誤', await eval_(`geometryFeedback.events.some(e=>e.k==='api'&&e.cmd.includes('place 999')&&!e.ok&&!!e.error)`));
  check('P38 回報鈕可見且不在頂列內', await eval_(`(()=>{const b=document.querySelector('#fbButton');const r=b.getBoundingClientRect();return r.width>0&&getComputedStyle(b).visibility==='visible'&&r.top>parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--topbar-h'))&&!document.querySelector('#app').contains(b)})()`));
  await pressKey('F8','F8',119);
  check('P38 F8 開面板且焦點在說明欄', await eval_(`!document.querySelector('#fbPanel').hidden && document.activeElement.id==='fbNote'`));
  await pressKey('Escape','Escape',27);
  check('P38 面板內 Esc 只關面板,不退出面工作區', await eval_(`document.querySelector('#fbPanel').hidden && oc.focus?.t==='face' && oc.focus.id===1`));
  await clickSelector('#fbButton');
  check('P38 回報鈕開面板', await eval_(`!document.querySelector('#fbPanel').hidden`));
  await send('Input.insertText',{text:'P38 測試:這裡怪怪的'});
  await clickSelector('[data-fb-kind="unexpected"]');
  const tabBefore = await eval_(`fe.fiTab`);
  await clickSelector('#fbPick');
  await clickSelector('#faceInspectorTabs [data-fi-tab="guide"]');
  check('P38 指出位置記下元素、且那一下沒有交給 app', await eval_(`!document.querySelector('#fbPanel').hidden && document.querySelector('#fbTarget').textContent.includes('data-fi-tab="guide"')`) && await eval_(`fe.fiTab`) === tabBefore);
  if (!fbDir) {
    console.log('P38 送出/自動擷取段略過:serve.py 未設 GEOMETRY_FEEDBACK_DIR(避免寫進 repo 的 feedback/)');
    await pressKey('Escape','Escape',27);
  } else {
    const before = fbList();
    await pressKey('Enter','Enter',13,2);
    for (let i=0;i<60 && fbList().length===before.length;i++) await sleep(100);
    const added = fbList().filter(n=>!before.includes(n));
    check('P38 Ctrl+Enter 送出後寫出一筆回報且面板關閉', added.length===1 && await eval_(`document.querySelector('#fbPanel').hidden`), added);
    if (added.length===1) {
      const m = fbMeta(added[0]); const d = require('path').join(fbDir, added[0]); const fs = require('fs');
      check('P38 回報帶分類、說明、指到的元素與畫面', m.kind==='unexpected' && m.note.includes('P38') && m.target.el.includes('data-fi-tab="guide"') && m.context.view.includes('面工作區 · 面 1'), m);
      check('P38 回報帶被拒指令、世界與紅框畫面快照',
        fs.readFileSync(require('path').join(d,'events.jsonl'),'utf8').includes('place 999') &&
        fs.readFileSync(require('path').join(d,'world.scene'),'utf8').includes('spec') &&
        fs.readFileSync(require('path').join(d,'page.html'),'utf8').includes('data-fb-target') &&
        !fs.readFileSync(require('path').join(d,'page.html'),'utf8').includes('<script'));
    }
    check('P38 送出後面板欄位已清空', await eval_(`document.querySelector('#fbNote').value==='' && document.querySelector('#fbTarget').textContent==='尚未指定元素'`));
    const before2 = fbList();
    await eval_(`setTimeout(()=>{throw new Error('fb-auto-probe')},0)`);
    for (let i=0;i<60 && fbList().length===before2.length;i++) await sleep(100);
    const auto = fbList().filter(n=>!before2.includes(n));
    check('P38 未捕捉的 JS 例外自動存一筆 kind=auto', auto.length===1 && fbMeta(auto[0]).kind==='auto' && fbMeta(auto[0]).auto_reason.includes('fb-auto-probe'), auto);
    const before3 = fbList();
    await eval_(`api('line place 998 on 1 at-line guide 1')`);
    await sleep(800);
    check('P38 規則拒絕(ok:false)不自動存', fbList().length===before3.length);
  }

  console.log('=== P39. 主畫布 Delete/Backspace 刪除選取的卡片 ===');
  const faceExists = id => eval_(`api("objects").then(r=>r.faces.some(f=>f.id===${id}))`);
  const selectCard = async id => { await eval_(`(()=>{selectObject("boundary",${id});document.activeElement&&document.activeElement.blur()})()`); await sleep(150); };
  await setupRemaining(['boundary 51 outline 0,0 1000,0 1000,800 0,800','canvas-pos boundary 51 60 60']);
  await selectCard(51);
  await pressKey('Delete','Delete',46);
  await sleep(300);
  check('P39 Delete 刪除選取的面', !(await faceExists(51)));
  check('P39 刪除後 toast 提示可復原', await eval_(`[...document.querySelectorAll('#toastRegion .toast')].some(t=>t.textContent.includes('51')&&t.textContent.includes('復原'))`));
  await pressKey('z','KeyZ',90,2);
  await sleep(300);
  check('P39 Ctrl+Z 復原被 Delete 刪掉的面', await faceExists(51));
  await eval_(`renderObjects()`); await sleep(200);
  await selectCard(51);
  await pressKey('Backspace','Backspace',8);
  await sleep(300);
  check('P39 Backspace 同樣刪除選取的面', !(await faceExists(51)));
  await pressKey('z','KeyZ',90,2); await sleep(300);
  await eval_(`renderObjects()`); await sleep(200);
  await selectCard(51);
  await eval_(`document.getElementById('searchInput').focus()`);
  await pressKey('Backspace','Backspace',8);
  check('P39 焦點在輸入框時 Backspace 不刪卡片', await faceExists(51));
  await eval_(`document.activeElement.blur()`);
  await selectCard(51);
  /* GEO-186(b) 後畫布只剩 rect 繪圖工具;繪圖工具備妥時 Delete/Backspace 一樣不刪卡片 */
  await eval_(`setOcTool('rect')`); await sleep(150);
  await eval_(`oc.sel={kind:'boundary',id:51}`);
  await pressKey('Backspace','Backspace',8);
  await pressKey('Delete','Delete',46);
  check('P39 矩形工具備妥時 Delete/Backspace 不刪卡片', await faceExists(51));
  await pressKey('Escape','Escape',27); await pressKey('Escape','Escape',27); await pressKey('Escape','Escape',27);
  await eval_(`(async()=>{resetSceneFocus();await api('default');await renderObjects()})()`);
  const p39Before = (await eval_(`apiRequest('dump')`)).text;
  await selectCard(1);
  /* 被引用的面:核心回 I8a 影響預覽,deleteObject 停在原生對話框等確認——不能用 pressKey(它會 waitIdle) */
  for (const type of ['keyDown','keyUp']) await send('Input.dispatchKeyEvent',{type,key:'Delete',code:'Delete',windowsVirtualKeyCode:46});
  for (let i=0;i<30 && !(await eval_(`!!document.querySelector('dialog.reference-impact[open]')`));i++) await sleep(100);
  check('P39 刪除被引用的面先跳影響預覽,不直接刪', await eval_(`!!document.querySelector('dialog.reference-impact[open]')`) && await faceExists(1));
  await pressKey('Escape','Escape',27);
  await sleep(300);
  check('P39 影響預覽 Esc 取消後世界不變', !(await eval_(`!!document.querySelector('dialog.reference-impact[open]')`)) && await faceExists(1) && (await eval_(`apiRequest('dump')`)).text === p39Before);

  console.log('=== P40. 建面 UI/UX 審查修正(GEO-185 存活路徑;GEO-186 後) ===');
  /* GEO-186(b) 移除畫布 P 工具後,原 P40 的多邊形格線(#polyGridSize)、閉合就緒浮標、
     Esc 暫存草稿、鍵入長度浮標等斷言隨機器一併移除(狀態機行為由 polydraft_test.js
     + §P35/P36 面內段覆蓋)。本節改驗 GEO-185 修正中仍存在於現行路徑的部分:
     一般格線間距、工具浮標不被 toast 蓋掉、建面成功單一 toast、放置表單預設軸。 */
  await send('Emulation.setDeviceMetricsOverride',{width:1382,height:860,deviceScaleFactor:1,mobile:false});
  await emptyWorld();
  await eval_(`oc.zoom=1;oc.panX=0;oc.panY=0;ocApply();setOcTool('select')`);
  const gridOf = () => eval_(`(()=>{const v=document.getElementById('canvasViewport');return {size:v.style.getPropertyValue('--grid-size'),cls:v.classList.contains('poly-snap-grid')}})()`);
  check('P40-1 一般模式格線 24 單位、無吸附格線類別', (await gridOf()).size === '24px' && !(await gridOf()).cls, await gridOf());
  /* rect 工具浮標不被 toast 蓋掉(原 P40-5 的存活路徑):R 啟用 → 單點出
     「請拖出範圍」toast → 浮標仍可見且 toast 排在浮標下方。
     先清掉前段殘留的 toast,只取這次點擊產生的那則。 */
  const o40 = await ocOrigin();
  await pressKey('r','KeyR',82); await sleep(150);
  await eval_(`document.querySelectorAll('#toastRegion .toast').forEach(t=>t.remove())`);
  await click(o40.x+600, o40.y+550); await sleep(300);
  const t40 = await eval_(`(()=>{const h=document.getElementById('canvasModeHint');
    const t=document.querySelector('#toastRegion .toast');
    return {hintVis:!h.hidden && getComputedStyle(h).visibility==='visible',
      hintBottom:h.getBoundingClientRect().bottom,
      toastTop:t?t.getBoundingClientRect().top:null,
      toastText:t?t.textContent:''};})()`);
  check('P40-2 rect 浮標在 toast 出現時仍可見、toast 排在浮標下方',
    t40.hintVis && t40.toastTop!==null && t40.toastTop>=t40.hintBottom && /拖出範圍/.test(t40.toastText), t40);
  /* 拖出矩形建面(objEmitFace):成功 toast 只有一則;新面放置表單預設 u=+x/v=+y、
     沒有「必須垂直」錯誤(原 P40-6/P40-8,改走矩形路徑) */
  await eval_(`document.querySelectorAll('#toastRegion .toast').forEach(t=>t.remove())`);
  await drag(o40.x+100, o40.y+100, o40.x+400, o40.y+350); await sleep(900);
  const made = await eval_(`({toasts:[...document.querySelectorAll('#toastRegion .toast')].filter(t=>t.textContent.includes('已建立')).length,
    v:document.querySelector('#placeV')?.value, u:document.querySelector('#placeU')?.value,
    err:[...document.querySelectorAll('#inspectorContent *, .inspector *')].some(e=>e.children.length===0&&e.textContent.includes('必須垂直'))})`);
  check('P40-3 建面成功只跳一則 toast', made.toasts===1, made);
  check('P40-4 新面的放置表單預設 u=+x、v=+y,沒有「必須垂直」錯誤', made.u==='+x' && made.v==='+y' && !made.err, made);
  await eval_(`setOcTool('select')`);

  console.log('=== P41. 縮到很小後找回卡片(GEO-187) ===');
  await setupRemaining(['boundary 61 outline 0,0 1000,0 1000,800 0,800','canvas-pos boundary 61 60 60',
    'boundary 62 outline 0,0 1000,0 1000,800 0,800','canvas-pos boundary 62 500 -3000']);
  const cardIn = id => eval_(`(()=>{const c=oroot.querySelector('.ocard[data-id="${id}"]');const r=c.getBoundingClientRect(),v=ocv.getBoundingClientRect();
    return {w:Math.round(r.width),inside:r.left>=v.left&&r.right<=v.right&&r.top>=v.top&&r.bottom<=v.bottom,zoom:oc.zoom}})()`);
  await eval_(`oc.zoom=0.02;oc.panX=300;oc.panY=300;ocApply()`);
  check('P41-1 縮到 2% 時格線間距不小於 8px(不再糊成灰色)', parseFloat(await eval_(`document.getElementById('canvasViewport').style.getPropertyValue('--grid-size')`)) >= 8);
  await eval_(`(()=>{selectObject('boundary',62);centerOnNode('boundary',62)})()`); await sleep(150);
  const loc = await cardIn(62);
  check('P41-2 縮很小時「定位卡片」會放大回 100% 並把卡片放進畫面', loc.zoom===1 && loc.inside && loc.w>=150, loc);
  await eval_(`oc.zoom=0.02;ocApply();centerOnNode('boundary',61);oc.zoom=0.02;(()=>{const c=cardCenter('boundary',61),r=ocv.getBoundingClientRect();oc.panX=r.width/2-c.x*oc.zoom;oc.panY=r.height/2-c.y*oc.zoom;ocApply()})()`);
  await clickSelector('#zoomLevelButton');
  const back = await cardIn(61);
  check('P41-3 點縮放比例回 100% 以畫面中心為準,中心的卡片不會飛出畫面', back.zoom===1 && back.inside, back);
  }

  chrome.kill();
  _log(`\n=== 結果:${passN} ✓ / ${failN} ✗ ===`);
  process.exit(failN > 0 ? 1 : 0);
})().catch(e => { console.log("FATAL:", e.message); chrome.kill(); process.exit(1); });
