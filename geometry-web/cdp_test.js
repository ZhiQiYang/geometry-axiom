/* CDP 驅動 headless Chrome 實測物件畫布互動 */
const { spawn } = require("child_process");
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9333;

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", `--remote-debugging-port=${PORT}`,
  "--window-size=1400,900", "--user-data-dir=C:\\tmp\\cdp-profile", "about:blank"
]);

const sleep = ms => new Promise(r => setTimeout(r, ms));
let ws, mid = 0, pending = {};

/* ✓/✗ 計數：所有印出的判定一律計入，exit code 依此決定。 */
let passN = 0, failN = 0;
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
          else if (m.method === "Runtime.exceptionThrown")
            console.log("[EXCEPTION]", JSON.stringify(m.params.exceptionDetails.exception?.description || m.params));
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
  for (const w of [1382, 1160]) {
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
    fileKids: ["btnOpen","btnScene","btnEx","btnClear"].every(id=>
      document.getElementById("fileMenu").contains(document.getElementById(id))),
    vsHasObj: document.getElementById("viewSwitch").contains(document.getElementById("btnObj")),
    zoomInCtl: document.querySelector(".canvas-controls").contains(document.getElementById("btnZoom")),
    kbd: document.querySelectorAll(".tool-group kbd").length
  })`);
  console.log("S2 結構:", JSON.stringify(s2),
    s2.searchInSide && s2.fileKids && s2.vsHasObj && s2.zoomInCtl && s2.kbd >= 4 ? "✓" : "✗");
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
  await sleep(1000);
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

  console.log("=== 9c. 「＋面·多邊形」逐點閉合 ===");
  await eval_(`document.getElementById("btnNewPoly").click()`);
  await sleep(200);
  const polyBase = await eval_(`(()=>{
    const r = document.getElementById("ocv").getBoundingClientRect();
    return {x: r.right - 320, y: r.top + 80};
  })()`);
  const fb2 = await eval_(`oc.faces.length`);
  /* L 形：右→下→右→下→左回起點 */
  await click(polyBase.x, polyBase.y);        await sleep(120);
  await click(polyBase.x + 120, polyBase.y);  await sleep(120);
  await click(polyBase.x + 120, polyBase.y + 60); await sleep(120);
  await click(polyBase.x + 60, polyBase.y + 60);  await sleep(120);
  await click(polyBase.x + 60, polyBase.y + 120); await sleep(120);
  await click(polyBase.x, polyBase.y + 120);  await sleep(120);
  await click(polyBase.x, polyBase.y);        await sleep(1200);  /* 點回起點閉合 */
  const fa2 = await eval_(`oc.faces.length`);
  console.log("faces:", fb2, "->", fa2, fa2 > fb2 ? "✓ 多邊形建面成功" : "✗ 失敗");
  console.log("status:", await eval_(`document.getElementById("status").textContent`));

  console.log("=== 9d. Ctrl+Z 復原 / Ctrl+Y 重做 ===");
  /* 最後兩步變更：boundary 3 建立 + 自動 canvas-pos。undo 兩次才回到面消失。 */
  const facesN = `oc.faces.length`;
  const fPreUndo = await eval_(facesN);
  const key = async (k, code, vk) => {
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: k, code, modifiers: 2, windowsVirtualKeyCode: vk });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, modifiers: 2, windowsVirtualKeyCode: vk });
  };
  await key("z", "KeyZ", 90); await sleep(800);
  const fU1 = await eval_(facesN);
  const st1 = await eval_(`document.getElementById("status").textContent`);
  console.log("undo1 api faces:", await eval_(`api("objects").then(r=>r.faces.length)`));
  await key("z", "KeyZ", 90); await sleep(800);
  const fU2 = await eval_(facesN);
  console.log("undo2 api faces:", await eval_(`api("objects").then(r=>r.faces.length)`));
  const st2 = await eval_(`document.getElementById("status").textContent`);
  console.log("undo×2:", fPreUndo, "->", fU1, "->", fU2,
              fU2 === fPreUndo - 1 ? "✓ undo 有效" : "✗", "|", st1, "|", st2);
  await key("y", "KeyY", 89); await sleep(800);
  await key("y", "KeyY", 89); await sleep(800);
  const fR2 = await eval_(facesN);
  console.log("redo×2:", fU2, "->", fR2, fR2 === fPreUndo ? "✓ redo 有效" : "✗");

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
    `[...document.querySelectorAll("#edgeGroup .edge-label")].map(t=>t.textContent).join(",")`));

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
  const gMatch = dump1 && dump1.match(/^guide (\d+) 20 v (-?\d+)$/m);
  console.log("guide:", gMatch ? `✓ guide ${gMatch[1]} 20 v ${gMatch[2]}` : "✗ dump 無 guide");
  /* 拖既有參考線 → move → offset 改變 */
  if (gMatch) {
    const gOff = +gMatch[2];
    const gPt = await eval_(`(()=>{
      const r = document.getElementById("faceEditorSvg").getBoundingClientRect();
      return {x: r.left + 100, y: r.top + (${gOff})*fe.zoom + fe.panY};
    })()`);
    await eval_(`document.querySelector('[data-face-tool="select"]').click()`);
    await sleep(200);
    await drag(gPt.x, gPt.y, gPt.x, gPt.y + 40);                /* 垂直往下拖 40px */
    await sleep(900);
    const dump2 = await eval_(`api("dump").then(r=>r.text)`);
    const g2 = dump2 && dump2.match(new RegExp("^guide " + gMatch[1] + " 20 v (-?\\d+)$", "m"));
    console.log("guide off:", gOff, "->", g2 && g2[1],
      g2 && +g2[1] !== gOff ? "✓ move 改變 offset" : "✗");
  }

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
    const g3 = d3 && d3.match(/^guide \d+ \d+ v -?\d+$/m);
    console.log("游離→放置後參考線:", g3 ? "✓ " + g3[0] : "✗");
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
    await api("line guide " + gid + " " + sid + " v 2000");
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
    window.confirm = () => true;
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
    $("tbLen").value = "1800"; $("tbA").value = "27"; $("tbB").value = "33";
    $("tbDir").value = "+u"; $("tbSide").value = "+n";
    feSetTool("timber");
    await feDown({x: 500, y: 300}, {target: $("faceEditorSvg"), clientX: 0, clientY: 0});
    await new Promise(r=>setTimeout(r,300));
    const dump1 = (await api("dump")).text;
    const hasTimber = /timber \\d+ 1800 27 33/.test(dump1) &&
                      /place \\d+ on \\d+ at 500 300 \\+u \\+n/.test(dump1);
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
    for (const b of dels) { b.click(); await new Promise(r=>setTimeout(r,200)); }
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
    `[...document.querySelectorAll("#edgeGroup .edge-label")].map(t=>t.textContent).join(",")`);
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
  /* 刪除 → 卡片消失 */
  await eval_(`window.confirm = () => true`);
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

  /* 點放柱:房間 (1500,500) → at 1200 200 size 600 */
  const ptCol = await eval_(`(()=>{
    const svg = document.getElementById("spacePlanSvg");
    const r = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
    return {x: r.left + (1500 - vb.x)/vb.width*r.width,
            y: r.top + (500 - vb.y)/vb.height*r.height};
  })()`);
  await click(ptCol.x, ptCol.y);
  await sleep(1000);
  const colP = await eval_(`api("objects").then(r=>({
    n: r.columns.length,
    dom: document.querySelectorAll("#spacePlanSvg .space-plan-col").length
  }))`);
  console.log("點放柱:", colP.n === 2 && colP.dom === 2
    ? "✓" : `✗ ${JSON.stringify(colP)}`);

  /* 拖放樑:水平拖 → along x */
  const bmD = await eval_(`(()=>{
    const svg = document.getElementById("spacePlanSvg");
    const r = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
    const px = (x,y)=>({x: r.left + (x - vb.x)/vb.width*r.width,
                       y: r.top + (y - vb.y)/vb.height*r.height});
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
  await sleep(1000);
  const obUi = await eval_(`({
    checks: document.querySelectorAll("#faceLayerList .fe-ob-check").length,
    checked: document.querySelectorAll("#faceLayerList .fe-ob-check:checked").length,
    btn: !!document.getElementById("feApplyProj"),
    cut: !!document.getElementById("feCutStrip"),
    btnTxt: document.getElementById("feApplyProj") &&
      document.getElementById("feApplyProj").textContent
  })`);
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
  await click(fbVp.cx, fbVp.cy);
  await sleep(400);
  const pkShown = await eval_(`!document.getElementById("feGuidePick").hidden`);
  console.log("參考線點一下→方向選單:", pkShown ? "✓" : "✗");
  const pkBtn = await eval_(`(()=>{const b=document.querySelector('#feGuidePick [data-axis="v"]');
    if(!b) return null; const r=b.getBoundingClientRect();
    return {x:r.left+r.width/2,y:r.top+r.height/2};})()`);
  if (pkBtn) { await click(pkBtn.x, pkBtn.y); await sleep(700); }
  const gDump = await eval_(`api("dump").then(d=>{const m=d.text.match(/^guide (\\d+) (\\d+) v (-?\\d+)$/m);return m&&m[0]})`);
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
  /* (e) 角材 L 空白 → toast + #tbLen 標紅 */
  await eval_(`(()=>{
    document.querySelector('[data-face-tool="timber"]').click();
    const tb=document.getElementById("tbLen"); if (tb) tb.value="";
  })()`);
  await sleep(250);
  await click(fbVp.qx, fbVp.qy);
  await sleep(350);
  const tbFb = await eval_(`({
    toast:[...document.querySelectorAll("#toastRegion .toast")].map(t=>t.textContent).join("|"),
    inv: document.getElementById("tbLen") && document.getElementById("tbLen").classList.contains("invalid")})`);
  console.log("角材L空→toast:", tbFb.toast.includes("長度") ? "✓" : "✗ " + tbFb.toast,
    "| tbLen標紅:", tbFb.inv ? "✓" : "✗");
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
  /* (c) poly 工具:點兩下 → 狀態列+浮標顯示頂點進度 */
  await eval_(`setOcTool("poly")`);
  await sleep(250);
  await click(ocPt.x, ocPt.y);
  await sleep(150);
  await click(ocPt.x + 60, ocPt.y);
  await sleep(250);
  const mh2 = await eval_(`(()=>({
    st: document.getElementById("status").textContent,
    hint: document.getElementById("canvasModeHint").textContent,
    vis: !document.getElementById("canvasModeHint").hidden}))()`);
  console.log("E7 poly 狀態列:", mh2.st.includes("2 頂點") ? "✓" : "✗ " + mh2.st,
    "| 浮標進度:", mh2.vis && mh2.hint.includes("2 頂點") ? "✓" : "✗ " + mh2.hint);
  /* (d) Esc 取消 → 浮標隱藏、草稿清空 */
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await sleep(300);
  const mh3 = await eval_(`(()=>({
    vis: !document.getElementById("canvasModeHint").hidden,
    tool: oc.drawTool, poly: oc.poly.length}))()`);
  console.log("E7 Esc 清草稿:", !mh3.vis && !mh3.tool && !mh3.poly ? "✓" : "✗ " + JSON.stringify(mh3));
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
    "| 鈕:", pf2.btn.includes("重綁") ? "✓" : "✗ " + pf2.btn);
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
      labels:[...document.querySelectorAll("#edgeGroup .edge-label")].map(t=>t.textContent)};})()`);
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
  /* (2) B2:三頁;切角材 → tbLen 可見 */
  const b2 = await eval_(`(()=>{
    const tabs=[...document.querySelectorAll("[data-fi-tab]")].map(t=>t.dataset.fiTab);
    document.querySelector('[data-fi-tab="timber"]').click();
    const tb=document.getElementById("tbLen");
    return {tabs, vis: !!tb && tb.offsetParent !== null};})()`);
  console.log("P18 B2 三頁:", b2.tabs.join() === "prop,timber,grid" ? "✓" : "✗ " + b2.tabs,
    "| 角材頁tbLen可見:", b2.vis ? "✓" : "✗");
  /* (3) B3:邊表方向文字+mm+segmented */
  const b3 = await eval_(`(()=>{
    document.querySelector('[data-fi-tab="prop"]').click();
    const rows=[...document.querySelectorAll(".edge-row")];
    return {n:rows.length,
      dir:rows.every(r=>/[→←↓↑]/.test(r.querySelector(".edge-dir").textContent)),
      mm:rows.every(r=>r.querySelector(".edge-mm").textContent.trim()==="mm"),
      seg:rows.every(r=>r.querySelectorAll(".fixity-btn").length===2),
      title:document.querySelector(".ib-sub") && document.querySelector(".ib-sub").textContent};})()`);
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
  /* (9) B9:麵包屑「空間 1 / 面 」+ 天花膠囊;游離面→游離 */
  const b9a = await eval_(`({
    eb:document.getElementById("workspaceEyebrow").textContent,
    cap:document.getElementById("workspacePlaceTag").textContent,
    capCls:document.getElementById("workspacePlaceTag").className,
    back:document.getElementById("workspaceBackLabel").textContent})`);
  if (b9a && b9a.__err) console.log("P18 B9 麵包屑: ✗ eval", b9a.__err);
  else console.log("P18 B9 麵包屑:", b9a.eb.includes("空間 1 / 面 ") ? "✓ " + b9a.eb : `✗ ${b9a.eb}`,
    "| 天花膠囊:", b9a.cap.includes("天花") ? "✓ " + b9a.cap : `✗ ${b9a.cap}`,
    "| 返回:", b9a.back.includes("物件畫布") ? "✓" : "✗");
  /* (10) 游離面:角材頁停用說明 + 游離膠囊 */
  await eval_(`enterFocus("face", 3)`);
  await sleep(700);
  const b9b = await eval_(`(()=>{
    document.querySelector('[data-fi-tab="timber"]').click();
    return {note:!!document.querySelector('[data-fi-pane="timber"] .fi-note'),
      cap:document.getElementById("workspacePlaceTag").textContent,
      tbDis:document.getElementById("tbLen").disabled};})()`);
  console.log("P18 游離停用說明:", b9b.note && b9b.tbDis ? "✓" : "✗ " + JSON.stringify(b9b),
    "| 游離膠囊:", b9b.cap.includes("游離") ? "✓" : "✗ " + b9b.cap);
  /* (11) 狀態列右側快捷鍵 L/R/Esc */
  const b11 = await eval_(`(()=>{
    const ks=[...document.querySelectorAll(".ws-kbd-hints kbd")].map(k=>k.textContent);
    return {L:ks.includes("L"),R:ks.includes("R"),Esc:ks.includes("Esc")};})()`);
  console.log("P18 快捷鍵列:", b11.L && b11.R && b11.Esc ? "✓" : "✗ " + JSON.stringify(b11));
  await eval_(`(async()=>{ if(oc.focus) await leaveFocus(); })()`);
  await sleep(400);

  console.log("=== 10. 三視圖覆層再開 ===");
  await eval_(`document.getElementById("btnObj").click()`);
  await sleep(800);
  console.log("cv hidden:", await eval_(`document.getElementById("cv").hasAttribute("hidden")`));
  console.log("world children:", await eval_(`document.getElementById("world").childElementCount`));
  chrome.kill();
  _log(`\n=== 結果:${passN} ✓ / ${failN} ✗ ===`);
  process.exit(failN > 0 ? 1 : 0);
})().catch(e => { console.log("FATAL:", e.message); chrome.kill(); process.exit(1); });
