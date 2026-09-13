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
  await send("Page.navigate", { url: "http://localhost:8765/" });
  await sleep(2500);
  /* 清世界 + 建一個乾淨的測試場：一片游離面、一個空容器 */
  await eval_(`api("line reset")`);
  await eval_(`api("line boundary 1 outline 0,0 4000,0 4000,3000 0,3000")`);
  await eval_(`api("line canvas-pos boundary 1 60 60")`);
  await sleep(500);

  console.log("=== 1. Phase 1 版面檢查點(§6) ===");
  /* (a) #app 三列:58 / 1fr / 28 */
  const rows = await eval_(`(()=>{const app=document.getElementById("app");
    const kids=[...app.children];return {n:kids.length,
      cls:kids.map(k=>k.className.split(" ")[0]).join(","),
      h:kids.map(k=>Math.round(k.getBoundingClientRect().height))}})()`);
  console.log("app rows:", JSON.stringify(rows),
    rows.n === 3 && rows.h[0] === 58 && rows.h[2] === 28 ? "✓ 三列殼" : "✗");
  /* (b) .workspace 三欄:左 242 / 中 1fr / 右 326 */
  const cols = await eval_(`(()=>{const w=document.querySelector(".workspace");
    const k=[...w.children];return {n:k.length,
      w:k.map(c=>Math.round(c.getBoundingClientRect().width))}})()`);
  console.log("workspace cols:", JSON.stringify(cols),
    cols.n === 3 && cols.w[0] === 242 && cols.w[2] === 326 ? "✓ 三欄" : "✗");
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
  /* 截圖存檔 */
  const shot = await send("Page.captureScreenshot", { format: "png" });
  require("fs").mkdirSync("docs/screens", { recursive: true });
  require("fs").writeFileSync("docs/screens/phase1-shell.png", Buffer.from((shot.result && shot.result.data) || "", "base64"));
  console.log("screenshot: docs/screens/phase1-shell.png");
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

  console.log("=== 10. 三視圖覆層再開 ===");
  await eval_(`document.getElementById("btnObj").click()`);
  await sleep(800);
  console.log("cv hidden:", await eval_(`document.getElementById("cv").hasAttribute("hidden")`));
  console.log("world children:", await eval_(`document.getElementById("world").childElementCount`));
  chrome.kill();
  _log(`\n=== 結果:${passN} ✓ / ${failN} ✗ ===`);
  process.exit(failN > 0 ? 1 : 0);
})().catch(e => { console.log("FATAL:", e.message); chrome.kill(); process.exit(1); });
