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
  require("fs").writeFileSync("phase1.png", Buffer.from((shot.result && shot.result.data) || "", "base64"));
  console.log("screenshot: phase1.png");
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
  const vtx = await eval_(`(()=>{
    if (!oc.focus || oc.focus.t !== "face" || !oc.edit) return null;
    const e = oc.edit, loops = oc.bmap[e.bid];
    if (!loops || !loops[0].verts.length) return null;
    const p = loops[0].verts[0];
    const r = ocv.getBoundingClientRect();
    return { x: r.left + p[0]*oc.zoom + oc.panX, y: r.top + p[1]*oc.zoom + oc.panY };
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

  console.log("=== 10. 三視圖覆層再開 ===");
  await eval_(`document.getElementById("btnObj").click()`);
  await sleep(800);
  console.log("cv hidden:", await eval_(`document.getElementById("cv").hasAttribute("hidden")`));
  console.log("world children:", await eval_(`document.getElementById("world").childElementCount`));
  chrome.kill();
  _log(`\n=== 結果:${passN} ✓ / ${failN} ✗ ===`);
  process.exit(failN > 0 ? 1 : 0);
})().catch(e => { console.log("FATAL:", e.message); chrome.kill(); process.exit(1); });
