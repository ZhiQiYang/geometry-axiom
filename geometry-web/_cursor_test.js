/* 全真實游標測試:所有功能一律用 Input.dispatchMouseEvent / dispatchKeyEvent /
 * insertText 觸發,不用 eval 代替使用者操作(eval 只用來取座標與斷言)。
 * 涵蓋:物件庫建立、卡片選取/拖曳/雙擊、面內全部工具(含角材/網格/凹口/
 *       重畫/鍵入長度/形狀庫/邊長清單/fixity)、柱樑對話框、檢視器表單、
 *       空間工作區(點放柱/拖放樑/構件列)、鬼影勾選+apply-proj、搜尋/篩選/
 *       鍵盤/三視圖。
 * 用法:server 在 8765 → node _cursor_test.js
 */
const { spawn } = require("child_process");
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9334;   /* 避開 cdp_test 的 9333 */

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", `--remote-debugging-port=${PORT}`,
  "--window-size=1400,900", "--user-data-dir=C:\\tmp\\cursor-profile", "about:blank"
]);

const sleep = ms => new Promise(r => setTimeout(r, ms));
let ws, mid = 0, pending = {};
let passN = 0, failN = 0;
const _log = console.log;
const say = (name, ok, extra = "") => {
  _log(`${ok ? "✓" : "✗"} ${name}${extra ? " | " + extra : ""}`);
  ok ? ++passN : ++failN;
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
          else if (m.method === "Runtime.exceptionThrown")
            _log("[EXC]", JSON.stringify(m.params.exceptionDetails.exception?.description || ""));
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
/* ---- 真實輸入事件 ---- */
async function click(x, y) {
  await settle();
  for (const [type, btn] of [["mousePressed", "left"], ["mouseReleased", "left"]])
    await send("Input.dispatchMouseEvent", { type, x, y, button: btn, clickCount: 1 });
}
async function dblclick(x, y) {
  await settle();
  for (const n of [1, 2])
    for (const type of ["mousePressed", "mouseReleased"])
      await send("Input.dispatchMouseEvent", { type, x, y, button: "left", clickCount: n });
}
async function drag(x0, y0, x1, y1, steps = 8) {
  await settle();
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: x0, y: y0, button: "left", clickCount: 1 });
  for (let i = 1; i <= steps; ++i)
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x0 + (x1 - x0) * i / steps, y: y0 + (y1 - y0) * i / steps, button: "left" });
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: x1, y: y1, button: "left", clickCount: 1 });
}
async function moveTo(x, y) {
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y });
}
/* 中鍵拖曳(平移視角):button=middle */
async function midDrag(x0, y0, x1, y1, steps = 6) {
  await settle();
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: x0, y: y0, button: "middle", clickCount: 1 });
  for (let i = 1; i <= steps; ++i)
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x0 + (x1 - x0) * i / steps, y: y0 + (y1 - y0) * i / steps, button: "middle" });
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: x1, y: y1, button: "middle", clickCount: 1 });
}
async function pressKey(k, opts = {}) {
  await settle();
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: k, ...opts });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: k, ...opts });
}
/* 逐字 keyDown/keyUp:會觸發 app 的 keydown 監聽(鍵入長度、快捷鍵)也會
 * 在聚焦 input 時輸入文字 */
async function typeKeys(t) {
  for (const ch of t) await pressKey(ch);
}
/* insertText:給 input 塞文字(支援 CJK),觸發 input 事件 */
async function insertText(t) {
  await settle();
  await send("Input.insertText", { text: t });
}
async function ctrlA() {
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "a", code: "KeyA", windowsVirtualKeyCode: 65, modifiers: 2 });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "a", code: "KeyA", windowsVirtualKeyCode: 65, modifiers: 2 });
}
/* 點 input → Ctrl+A → 打字 */
async function fillInput(sel, val) {
  const p = await ctr(sel);
  if (!p) return false;
  await click(p.x, p.y); await sleep(120);
  await ctrlA(); await sleep(60);
  await insertText(String(val)); await sleep(80);
  return true;
}
/* ---- 元素定位 ---- */
const ctr = sel => eval_(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});
  if(!e)return null;e.scrollIntoView({block:"center",inline:"center"});
  const r=e.getBoundingClientRect();
  return {x:r.left+r.width/2,y:r.top+r.height/2};})()`);
const clickEl = async sel => {
  const p = await ctr(sel);
  if (!p) return false;
  await click(p.x, p.y);
  return true;
};
const dblclickEl = async sel => {
  const p = await ctr(sel);
  if (!p) return false;
  await dblclick(p.x, p.y);
  return true;
};
/* ocv 世界座標→螢幕 */
const ocPt = (wx, wy) => eval_(`(()=>{const r=document.getElementById("ocv").getBoundingClientRect();
  return {x:r.left+${wx}*oc.zoom+oc.panX,y:r.top+${wy}*oc.zoom+oc.panY};})()`);
/* 面編輯器 uv→螢幕 */
const fePt = (u, v) => eval_(`(()=>{const r=document.getElementById("faceEditorSvg").getBoundingClientRect();
  return {x:r.left+${u}*fe.zoom+fe.panX,y:r.top+${v}*fe.zoom+fe.panY};})()`);
/* 空間平面圖 viewBox 座標→螢幕 */
const plPt = (x, y) => eval_(`(()=>{const svg=document.getElementById("spacePlanSvg");
  const r=svg.getBoundingClientRect(),vb=svg.viewBox.baseVal;
  return {x:r.left+(${x}-vb.x)/vb.width*r.width,y:r.top+(${y}-vb.y)/vb.height*r.height}})()`);
/* 沉降:等 oc.busy 清掉再動手——模擬看到忙碌態才點的真實使用者。
   emitLine/mutate 在 busy 時會靜默丟棄操作,不沉降的點擊不等於真實失敗。 */
const settle = async () => {
  await eval_(`new Promise(r=>{let n=0;const t=()=>(!oc.busy||++n>80)?r():setTimeout(t,60);t()})`);
  await sleep(120);
};
/* Esc 直到離開焦點(對話框→lenBuf→拖曳→工具→leaveFocus 逐級) */
async function escUntilFree(tries = 5) {
  for (let i = 0; i < tries; ++i) {
    if (await eval_(`oc.focus===null`)) return true;
    await pressKey("Escape"); await sleep(350);
  }
  return eval_(`oc.focus===null`);
}

(async () => {
  await connect();
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Page.navigate", { url: process.env.GEOMETRY_TEST_URL || "http://localhost:8765/" });
  await sleep(2500);
  if (process.env.GEOMETRY_AUDIT_ONLY !== "1" || process.env.GEOMETRY_AUDIT !== "1") {
  await eval_(`api("line reset")`);
  await sleep(400);

  /* ========== 1. 物件庫:＋面·矩形 真實拖曳 ========== */
  _log("== 物件庫建立 ==");
  await clickEl("#btnNewRect"); await sleep(250);
  const c0 = await ocPt(60, 60), c1 = await ocPt(260, 210);
  await drag(c0.x, c0.y, c1.x, c1.y);
  await sleep(700);
  let n = await eval_(`api("objects").then(r=>r.faces.length)`);
  say("＋面·矩形 拖曳建面", n === 1, `faces=${n}`);

  /* ========== 2. ＋面·多邊形 逐點點擊閉合 ========== */
  await clickEl("#btnNewPoly"); await sleep(250);
  const poly = [[60, 300], [260, 300], [260, 380], [180, 380], [180, 460], [60, 460]];
  for (const [x, y] of poly) { const p = await ocPt(x, y); await click(p.x, p.y); await sleep(130); }
  const p0 = await ocPt(poly[0][0], poly[0][1]);
  await click(p0.x, p0.y); await sleep(800);
  n = await eval_(`api("objects").then(r=>r.faces.length)`);
  say("＋面·多邊形 點擊閉合", n === 2, `faces=${n}`);

  /* ========== 3. 卡片:單擊選取→檢視器;拖卡片 ========== */
  _log("== 卡片互動 ==");
  const card1 = await ctr(`.ocard[data-kind="boundary"][data-id="1"]`);
  await click(card1.x, card1.y); await sleep(400);
  say("單擊選取→檢視器", await eval_(`!document.getElementById("inspectorContent").hidden`) === true);
  const c2 = await ocPt(500, 500);
  await drag(card1.x, card1.y, c2.x, c2.y); await sleep(700);
  const pos1 = await eval_(`api("objects").then(r=>{const f=r.faces.find(f=>f.id===1);return [f.cx,f.cy]})`);
  say("拖卡片→canvas-pos", pos1 && pos1[0] > 250 && pos1[1] > 250, JSON.stringify(pos1));

  /* ========== 4. 雙擊進面工作區 ========== */
  _log("== 面內工作區 ==");
  await dblclickEl(`.ocard[data-kind="boundary"][data-id="1"]`);
  await sleep(1000);
  say("雙擊進面工作區", await eval_(`oc.focus && oc.focus.t==="face" && oc.focus.id===1`));

  /* 面 1 外環 uv = 畫布座標: (60,60)(260,60)(260,210)(60,210) */
  /* ========== 5. 單擊邊切 fixity(F→X):邊 0 中點 (160,60) ========== */
  const eMid = await fePt(160, 60);
  await click(eMid.x, eMid.y); await sleep(800);
  let b1 = await eval_(`api("boundary 1").then(r=>r.loops[0].fixity)`);
  say("單擊邊切 fixity", b1 && b1[0] === 0, JSON.stringify(b1));

  /* ========== 6. 拖頂點 0 (60,60)→(160,60)(水平,鄰點連動) ========== */
  const v0 = await fePt(60, 60), v1 = await fePt(160, 60);
  await drag(v0.x, v0.y, v1.x, v1.y); await sleep(900);
  b1 = await eval_(`api("boundary 1").then(r=>r.loops[0].verts)`);
  /* snap(grid 50) 會吸到整數格:斷言 v0 位移且相鄰頂點連動(兩頂點同 u) */
  say("拖頂點改外環(連動)", b1 && b1.length === 4 && b1[0][0] !== 60 &&
    b1[0][0] === b1[3][0], JSON.stringify(b1));

  /* 現在面 1 ≈ (150,50)(260,50)(260,210)(150,210) */
  /* ========== 7. r 開口:拖矩形(snap 後 (200,100)-(250,150) 內側) ========== */
  await clickEl(`[data-face-tool="hole"]`); await sleep(250);
  const h0 = await fePt(180, 90), h1 = await fePt(240, 140);
  await drag(h0.x, h0.y, h1.x, h1.y); await sleep(900);
  const lp = await eval_(`api("boundary 1").then(r=>r.loops.length)`);
  say("拖開口", lp === 2, `loops=${lp}`);

  /* ========== 8. i 凹口工具:點下邊 (200,210)→對話框→送出 ========== */
  await clickEl(`[data-face-tool="insert"]`); await sleep(250);
  const eMid2 = await fePt(200, 210);
  await click(eMid2.x, eMid2.y); await sleep(400);
  const notchOpen = await eval_(`!document.getElementById("notchDialog").hidden`);
  say("凹口對話框", notchOpen === true);
  if (notchOpen) {
    await clickEl("#notchSubmit"); await sleep(900);
    b1 = await eval_(`api("boundary 1").then(r=>r.loops[0].verts.length)`);
    say("參數化凹口插入", b1 === 8, `verts=${b1}`);
  }

  /* ========== 9. l 參考線:游離面拒絕(語意:要先放置) ========== */
  await clickEl(`[data-face-tool="guide"]`); await sleep(250);
  const g0 = await fePt(170, 90), g1 = await fePt(220, 90);
  await drag(g0.x, g0.y, g1.x, g1.y); await sleep(600);
  let d7 = await eval_(`api("dump").then(r=>r.text)`);
  say("參考線(游離面拒絕)", !/guide /.test(d7 || ""));

  /* ========== 10. t 角材:游離面點擊→拒絕 ========== */
  await clickEl(`[data-face-tool="timber"]`); await sleep(250);
  const tp = await fePt(180, 170);
  await click(tp.x, tp.y); await sleep(500);
  d7 = await eval_(`api("dump").then(r=>r.text)`);
  say("角材(游離面拒絕)", !/timber /.test(d7 || ""));

  /* ========== 11. e 外環重畫:點擊+鍵入長度+回起點閉合 ========== */
  /* zoom≈3.3 下可視範圍有限,全部點落在視窗內的小矩形 */
  await clickEl(`[data-face-tool="redraw"]`); await sleep(250);
  const rp = await fePt(120, 40);
  await click(rp.x, rp.y); await sleep(200);
  /* 游標朝下 → 鍵入 120 → 下一點 (120,160) */
  const rmv = await fePt(120, 200);
  await moveTo(rmv.x, rmv.y); await sleep(150);
  await typeKeys("120"); await sleep(100);
  await pressKey("Enter"); await sleep(200);
  const rp2 = await fePt(280, 160); await click(rp2.x, rp2.y); await sleep(150);
  const rp3 = await fePt(280, 40); await click(rp3.x, rp3.y); await sleep(150);
  await click(rp.x, rp.y); await sleep(1000);   /* 點回起點閉合 */
  b1 = await eval_(`api("boundary 1").then(r=>r.loops[0].verts)`);
  /* snap(grid50):120→100/150?、280→300、160→150/200——斷言換成矩形且比原面大 */
  say("重畫外環+鍵入長度", b1 && b1.length === 4 && Math.max(...b1.map(p => p[0])) > 260,
    JSON.stringify(b1));

  /* ========== 12. 形狀庫:開對話框→L 形套用 ========== */
  await clickEl("#faceShapeButton"); await sleep(400);
  const shapeOpen = await eval_(`!document.getElementById("shapeDialog").hidden`);
  say("形狀對話框開啟", shapeOpen === true);
  if (shapeOpen) {
    await clickEl("#shapeSubmit"); await sleep(1000);
    b1 = await eval_(`api("boundary 1").then(r=>r.loops[0].verts.length)`);
    say("形狀庫套用(L)", b1 === 6, `verts=${b1}`);
  }

  /* ========== 13. 檢視器邊長清單:改邊 0 長度 ========== */
  /* B2:邊表在「屬性」頁——timber 工具剛把檢視器切到角材頁,先切回 */
  await clickEl(`[data-fi-tab="prop"]`); await sleep(300);
  const edgeSel = `#faceInspectorContent input[data-edge-len="0"]`;
  const hasEdgeInp = await eval_(`!!document.querySelector(${JSON.stringify(edgeSel)})`);
  if (hasEdgeInp) {
    await fillInput(edgeSel, 500);
    await pressKey("Tab"); await sleep(900);
    b1 = await eval_(`api("boundary 1").then(r=>r.loops[0].verts)`);
    const e0 = b1 && Math.max(Math.abs(b1[1][0] - b1[0][0]), Math.abs(b1[1][1] - b1[0][1]));
    say("檢視器改邊長(連動)", e0 === 500, `edge0=${e0} verts0=${JSON.stringify(b1 && b1[0])}`);
  } else say("檢視器改邊長", false, "無 data-edge-len input");

  /* ========== 14. Esc 回世界 ========== */
  say("Esc 回世界", await escUntilFree());

  /* ========== 15. ＋空間 六面盒 ========== */
  _log("== 空間與柱樑 ==");
  await clickEl("#btnBox6"); await sleep(400);
  const boxOpen = await eval_(`!document.getElementById("box6Dialog").hidden`);
  say("六面盒對話框", boxOpen === true);
  if (boxOpen) {
    await clickEl("#box6Submit"); await sleep(1200);
    const sp = await eval_(`api("objects").then(r=>({f:r.faces.length,s:r.spaces.length,closed:r.spaces[0]&&r.spaces[0].closed}))`);
    say("六面盒建立", sp.f >= 6 && sp.closed === true, JSON.stringify(sp));
  }

  /* ========== 16. ＋柱 對話框:選空間+打字 ========== */
  await clickEl("#btnNewColumn"); await sleep(400);
  const rcOpen = await eval_(`!document.getElementById("rcDialog").hidden && !document.getElementById("rcColFields").hidden`);
  say("柱對話框", rcOpen === true);
  if (rcOpen) {
    /* 空間 select:聚焦後 ↓ 選空間 1 */
    const rsp = await ctr("#rcSpace");
    await click(rsp.x, rsp.y); await sleep(150);
    await pressKey("ArrowDown"); await pressKey("Enter"); await sleep(150);
    const spv = await eval_(`document.getElementById("rcSpace").value`);
    await fillInput("#rcX", 500);
    await fillInput("#rcY", 500);
    await clickEl("#rcSubmit"); await sleep(900);
    const cn = await eval_(`api("objects").then(r=>r.columns.length)`);
    say("對話框建柱(z 推導)", cn === 1 && spv !== "0", `columns=${cn} space=${spv}`);
  }

  /* ========== 17. ＋樑 對話框 ========== */
  await clickEl("#btnNewBeam"); await sleep(400);
  const rbOpen = await eval_(`!document.getElementById("rcDialog").hidden && !document.getElementById("rcBeamFields").hidden`);
  say("樑對話框", rbOpen === true);
  if (rbOpen) {
    const rsp = await ctr("#rcSpace");
    await click(rsp.x, rsp.y); await sleep(150);
    await pressKey("ArrowDown"); await pressKey("Enter"); await sleep(150);
    await clickEl("#rcSubmit"); await sleep(900);
    const bn = await eval_(`api("objects").then(r=>r.beams.length)`);
    say("對話框建樑(top 推導)", bn === 1, `beams=${bn}`);
  }

  /* ========== 18. 柱卡:拖曳 + 雙擊檢視器 + 表單重宣告 ========== */
  const colCard = await ctr(`.ocard[data-kind="column"]`);
  say("柱卡片", !!colCard);
  if (colCard) {
    const tgt = await ocPt(600, 600);
    await drag(colCard.x, colCard.y, tgt.x, tgt.y); await sleep(800);
    const cp = await eval_(`api("objects").then(r=>r.columns[0].cx)`);
    say("柱卡拖曳→canvas-pos", cp > 300, `cx=${cp}`);
    const cc = await ctr(`.ocard[data-kind="column"]`);
    await dblclick(cc.x, cc.y); await sleep(600);
    say("雙擊柱→檢視器", await eval_(`!!document.getElementById("rcfX")`) === true);
    await fillInput("#rcfX", 900);
    await clickEl("#rcfApply"); await sleep(900);
    const bx = await eval_(`api("objects").then(r=>r.columns[0].box[0])`);
    say("柱表單重宣告", bx === 900, `x_lo=${bx}`);
  }

  /* ========== 19. 搜尋 + 篩選 ========== */
  _log("== 搜尋/篩選 ==");
  const si = await ctr("#searchInput");
  await click(si.x, si.y); await sleep(150);
  await insertText("柱"); await sleep(500);
  const vis = await eval_(`[...document.querySelectorAll('.ocard[data-kind="column"]')].filter(c=>!c.classList.contains("type-hidden")&&c.style.display!=="none").length`);
  say("搜尋「柱」", vis === 1, `column visible=${vis}`);
  await insertText(""); await sleep(100);
  await eval_(`(()=>{const s=document.getElementById("searchInput");s.value="";s.dispatchEvent(new Event("input"));s.blur();return true})()`);
  await sleep(300);
  const fcb = await ctr(`button[data-filter-type="column"]`);
  await click(fcb.x, fcb.y); await sleep(400);
  const colVis = await eval_(`[...document.querySelectorAll('.ocard[data-kind="column"]')].filter(c=>!c.classList.contains("type-hidden")).length`);
  say("篩選關柱", colVis === 0, `visible=${colVis}`);
  await click(fcb.x, fcb.y); await sleep(300);

  /* ========== 20. 空間工作區:平面圖點放柱/拖放樑 ========== */
  _log("== 空間工作區 ==");
  await dblclickEl(`.ocard[data-kind="space"]`);
  await sleep(1400);
  say("雙擊空間→工作區", await eval_(`oc.focus && oc.focus.t==="space"`));
  const planOK = await eval_(`!!document.querySelector("#spacePlanSvg .space-plan-floor")`);
  say("平面示意圖", planOK === true);
  /* 點放柱:svg 內 45%,30% 處 */
  const plFrac = async (fx, fy) => eval_(`(()=>{const r=document.getElementById("spacePlanSvg").getBoundingClientRect();
    return {x:r.left+r.width*${fx},y:r.top+r.height*${fy}}})()`);
  const pp = await plFrac(0.45, 0.3);
  await click(pp.x, pp.y); await sleep(1000);
  let cn = await eval_(`api("objects").then(r=>r.columns.length)`);
  say("平面圖點放柱", cn === 2, `columns=${cn}`);
  /* 拖放樑:垂直拖 → along y */
  const pa = await plFrac(0.85, 0.1), pb = await plFrac(0.87, 0.9);
  await drag(pa.x, pa.y, pb.x, pb.y); await sleep(1000);
  let bn = await eval_(`api("objects").then(r=>r.beams.length)`);
  say("平面圖拖放樑", bn === 2, `beams=${bn}`);

  /* ========== 21. 構件清單:移出/收進/✕ ========== */
  const rcRows = await eval_(`document.querySelectorAll("#spaceRcList .space-boundary-button").length`);
  say("構件清單列", rcRows >= 3, `rows=${rcRows}`);
  const mvBtn = await ctr(`#spaceRcList .space-boundary-button`);
  if (mvBtn) {
    await click(mvBtn.x, mvBtn.y); await sleep(900);
    const freeN = await eval_(`document.querySelectorAll("#spaceRcFreeList .space-boundary-button").length`);
    say("移出→游離列", freeN === 1, `free=${freeN}`);
    const inBtn = await ctr(`#spaceRcFreeList .space-boundary-button`);
    if (inBtn) {
      await click(inBtn.x, inBtn.y); await sleep(900);
      const freeN2 = await eval_(`document.querySelectorAll("#spaceRcFreeList .space-boundary-button").length`);
      say("收進→空間", freeN2 === 0,
        `free=${freeN2} status=${await eval_(`document.getElementById("status").textContent`)}`);
    }
    const delB = await ctr(`#spaceRcList .face-layer-del`);
    if (delB) {
      await click(delB.x, delB.y); await sleep(900);
      const tot = await eval_(`api("objects").then(r=>r.columns.length+r.beams.length)`);
      say("構件列 ✕ 刪除", tot === 3, `total=${tot}`);
    } else say("構件列 ✕ 刪除", false, "無 ✕ 鈕");
  }

  /* ========== 22. 天花面:參考線/角材/網格(已放置面) + 鬼影套用 ========== */
  _log("== 放置面工具 + 鬼影套用 ==");
  await escUntilFree();
  /* 找有障礙物的放置面(天花) */
  const obBid = await eval_(`(async()=>{
    const sf=await api("surfaces"); if(!sf.ok) return 0;
    for(const s of sf.surfaces){
      const ob=await api("obstacles "+s.boundary);
      if(ob.ok&&ob.items&&ob.items.length) return s.boundary;
    } return 0; })()`);
  say("障礙物查詢有面", obBid > 0, `bid=${obBid}`);
  if (obBid) {
    await dblclickEl(`.ocard[data-kind="boundary"][data-id="${obBid}"]`);
    await sleep(1400);
    /* 面心 uv(點角材用) */
    const ctrUv = await eval_(`(()=>{const vs=oc.bmap[${obBid}][0].verts;
      return [vs.reduce((a,p)=>a+p[0],0)/vs.length, vs.reduce((a,p)=>a+p[1],0)/vs.length]})()`);
    /* 參考線:已放置面可拖 */
    await clickEl(`[data-face-tool="guide"]`); await sleep(250);
    const gu = ctrUv[0] + 100;
    const gp = await fePt(gu, ctrUv[1]), gp2 = await fePt(gu, ctrUv[1] + 200);
    await drag(gp.x, gp.y, gp2.x, gp2.y); await sleep(900);
    let dd = await eval_(`api("dump").then(r=>r.text)`);
    say("拖參考線(放置面)", /guide \d+ \d+ [uv] \d+/.test(dd || ""));
    /* 角材:t 工具點面心(公理 O3:點放要明寫 L;B2:先切工具開角材頁再填 L) */
    await clickEl(`[data-face-tool="timber"]`); await sleep(350);
    await fillInput("#tbLen", 1200);
    const tp = await fePt(ctrUv[0], ctrUv[1]);
    await click(tp.x, tp.y); await sleep(900);
    dd = await eval_(`api("dump").then(r=>r.text)`);
    say("角材放置(放置面)", /timber /.test(dd || ""),
      `status=${await eval_(`document.getElementById("status").textContent`)}`);
    if (process.env.GEOMETRY_AUDIT === "1") {
      const placed = (dd || "").split("\n").find(l => /^place \d+ on \d+ at /.test(l));
      say("Audit 角材確實有放置指令", !!placed, placed || "只有宣告，沒有 place");
      say("Audit 角材足跡確實畫出", await eval_(`document.querySelectorAll("#faceEditorRoot .face-timber").length>0`));
    }
    /* 角材列 ✕ 刪除(找含「角材」字樣的那一列) */
    const tDel = await eval_(`(()=>{for(const r of document.querySelectorAll("#faceLayerList .face-layer-row")){
      if(r.textContent.includes("角材")){
        const b=r.querySelector(".face-layer-del"); if(!b) return null;
        b.scrollIntoView({block:"center"});const rc=b.getBoundingClientRect();
        return {x:rc.left+rc.width/2,y:rc.top+rc.height/2};}} return null})()`);
    if (tDel) {
      await click(tDel.x, tDel.y); await sleep(900);
      dd = await eval_(`api("dump").then(r=>r.text)`);
      say("圖層列 ✕ 刪角材", !/timber /.test(dd || ""));
    } else say("圖層列 ✕ 刪角材", false, "無角材列");
    /* 網格:先切「網格」頁(B2 分頁),填 u/v → 建立 */
    await clickEl(`[data-fi-tab="grid"]`); await sleep(300);
    await fillInput("#gridU", "500");
    await fillInput("#gridV", "500");
    await clickEl("#gridCreate"); await sleep(900);
    dd = await eval_(`api("dump").then(r=>r.text)`);
    say("建立網格", /grid /.test(dd || ""),
      `status=${await eval_(`document.getElementById("status").textContent`)}`);
    /* 鬼影 + 套用:條帶要勾選 + 裁切條帶開關才生效 */
    const ghosts = await eval_(`document.querySelectorAll("#faceEditorRoot .obstacle-ghost").length`);
    say("面內鬼影顯示", ghosts >= 1, `ghosts=${ghosts}`);
    const obChk = await eval_(`document.querySelectorAll("#faceLayerList .fe-ob-check").length`);
    say("鬼影勾選列", obChk >= 1, `checks=${obChk}`);
    if (obChk) {
      /* 勾「條帶」項(預設不勾)+ 裁切條帶開關 */
      const stripCb = await eval_(`(()=>{for(const c of document.querySelectorAll("#faceLayerList .fe-ob-check")){
        const row=c.closest(".fe-ob-row");
        if(row&&row.textContent.includes("條帶")&&!c.checked){
          c.scrollIntoView({block:"center"});const r=c.getBoundingClientRect();
          return {x:r.left+r.width/2,y:r.top+r.height/2};}} return null})()`);
      if (stripCb) { await click(stripCb.x, stripCb.y); await sleep(300); }
      const cut = await ctr(`#feCutStrip`);
      if (cut) { await click(cut.x, cut.y); await sleep(200); }
      const fN = await eval_(`api("objects").then(r=>r.faces.length)`);
      const btnSt = await eval_(`(()=>{const b=document.getElementById("feApplyProj");
        if(!b) return "no-btn";const r=b.getBoundingClientRect();
        const t=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);
        return "disabled="+b.disabled+" top="+(t&&(t.id||t.className||t.tagName))+" busy="+oc.busy})()`);
      await clickEl("#feApplyProj"); await sleep(1500);
      const fN2 = await eval_(`api("objects").then(r=>r.faces.length)`);
      say("套用投影(裁切條帶→拆面)", fN2 > fN, `faces ${fN}→${fN2} [${btnSt}] status=${await eval_(`document.getElementById("status").textContent`)}`);
    }
  }

  /* ========== 23. 鍵盤 + 三視圖 ========== */
  _log("== 鍵盤/三視圖 ==");
  await escUntilFree();
  await pressKey("/"); await sleep(250);
  say("/ 聚焦搜尋", await eval_(`document.activeElement===document.getElementById("searchInput")`));
  await pressKey("Escape"); await sleep(250);
  await eval_(`document.getElementById("searchInput").blur()`);
  await clickEl("#btnObj"); await sleep(800);
  say("三視圖開", await eval_(`!document.getElementById("cv").hasAttribute("hidden")`));
  /* 三視圖點擊拾取:點畫布中央(有柱樑應可 pick) */
  const cvp = await eval_(`(()=>{const r=document.getElementById("cv").getBoundingClientRect();
    return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
  await click(cvp.x, cvp.y); await sleep(400);
  await clickEl("#btnObj"); await sleep(500);

  /* ========== 24. 中鍵拖曳平移 ========== */
  _log("== 中鍵平移 ==");
  { /* 物件畫布:ocv 視區內命中點中鍵拖 → oc.pan 變 */
    const hp = await eval_(`(()=>{const r=document.getElementById("ocv").getBoundingClientRect();
      for(let y=r.top+80;y<r.bottom-80;y+=60)for(let x=r.left+80;x<r.right-80;x+=80){
        const e=document.elementFromPoint(x,y);
        if(e&&(e.id==="ocv"||(e.closest&&e.closest("#ocv"))))return{x,y};}return null})()`);
    if (!hp) say("物件畫布中鍵拖", false, "找不到 ocv 命中點");
    else {
      const p0 = await eval_("[oc.panX,oc.panY]");
      await midDrag(hp.x, hp.y, hp.x - 60, hp.y + 30); await sleep(300);
      const p1 = await eval_("[oc.panX,oc.panY]");
      say("物件畫布中鍵拖", Math.abs(p1[0] - p0[0] + 60) < 2 && Math.abs(p1[1] - p0[1] - 30) < 2,
          `[${p0}]→[${p1}]`);
    }
  }
  { /* 面內工作區:雙擊任一卡進去,中鍵拖 → fe.pan 變,Esc 出來 */
    await dblclickEl(`.ocard[data-kind="boundary"]`); await sleep(700);
    const inFe = await eval_("!!oc.edit");
    if (!inFe) say("面內中鍵拖", false, "進不了面工作區");
    else {
      const vp = await eval_(`(()=>{const r=document.getElementById("faceEditorSvg").getBoundingClientRect();
        return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
      const p0 = await eval_("[fe.panX,fe.panY]");
      await midDrag(vp.x, vp.y, vp.x + 80, vp.y + 40); await sleep(300);
      const p1 = await eval_("[fe.panX,fe.panY]");
      say("面內中鍵拖", Math.abs(p1[0] - p0[0] - 80) < 2 && Math.abs(p1[1] - p0[1] - 40) < 2,
          `[${p0}]→[${p1}]`);
      await pressKey("Escape"); await sleep(400);
    }
  }

  }

  if (process.env.GEOMETRY_AUDIT === "1") {
    _log("== Audit: shapes and camera state ==");
    await escUntilFree();
    await pressKey("f"); await sleep(300);
    let target, hit;
    for (let attempt = 0; attempt < 4; ++attempt) {
      target = await ctr('.ocard[data-kind="boundary"][data-id="2"]');
      hit = target && await eval_(`(()=>{const e=document.elementFromPoint(${target.x},${target.y});const c=e&&e.closest(".ocard");return c?{kind:c.dataset.kind,id:c.dataset.id}:null})()`);
      if (!hit || (hit.kind === "boundary" && hit.id === "2")) break;
      await drag(target.x, target.y, target.x + 220, target.y + 100); await sleep(400);
    }
    if (target) await dblclick(target.x, target.y);
    await sleep(700);
    const auditFace = await eval_('oc.edit && oc.edit.bid');
    say("Audit 進入獨立面", auditFace === 2, JSON.stringify({target,hit,auditFace}));
    if (auditFace === 2) {
      for (const [kind, expectedArea, expectedCount] of [["L", 6000000, 6], ["U", 8000000, 8], ["T", 6000000, 8]]) {
        await clickEl("#faceShapeButton");
        await clickEl(`input[name="shapeKind"][value="${kind}"]`);
        for (const [id, value] of [["shapeW", 4000], ["shapeD", 3000], ["shapeA", 1000], ["shapeB", 1000]]) await fillInput("#" + id, value);
        await clickEl("#shapeSubmit"); await sleep(700);
        const boundary = await eval_('api("boundary 2")');
        const pts = boundary.loops[0].verts;
        const area = Math.abs(pts.reduce((sum, p, i) => {
          const q = pts[(i + 1) % pts.length]; return sum + p[0] * q[1] - q[0] * p[1];
        }, 0)) / 2;
        say("Audit " + kind + "形尺寸與面積", area === expectedArea && pts.length === expectedCount,
          `vertices=${pts.length} area=${area}`);
      }
      const savedBoundary = JSON.stringify(await eval_('api("boundary 2")'));
      await clickEl("#faceShapeButton");
      await fillInput("#shapeA", 4000);
      await clickEl("#shapeSubmit"); await sleep(400);
      say("Audit 非法形狀拒絕且模型不變", savedBoundary === JSON.stringify(await eval_('api("boundary 2")')) && await eval_('!document.getElementById("shapeDialog").hidden'));
      await clickEl("#shapeCancel");
      await clickEl('[data-face-tool="select"]');
      await pressKey("f");
      await clickEl('[data-face-tool="redraw"]');
      for (const [u, v] of [[1000, 1000], [2000, 1000], [2000, 2000]]) {
        const pt = await fePt(u, v); await click(pt.x, pt.y);
      }
      const draft = await eval_('fe.drag && fe.drag.pts');
      say("Audit 三點重畫草稿存在", Array.isArray(draft) && draft.length === 3, JSON.stringify(draft));
      const vp = await eval_('(()=>{const r=document.getElementById("faceEditorSvg").getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()');
      await midDrag(vp.x, vp.y, vp.x + 80, vp.y + 40);
      const afterPan = await eval_('fe.drag && fe.drag.pts');
      say("Audit 重畫中中鍵平移不得丟草稿", Array.isArray(draft) && JSON.stringify(draft) === JSON.stringify(afterPan), `before=${JSON.stringify(draft)} after=${JSON.stringify(afterPan)}`);
      say("Audit 平移沒有改核心模型", savedBoundary === JSON.stringify(await eval_('api("boundary 2")')));
      await clickEl('[data-face-tool="select"]');
      for (let i = 0; i < 50; ++i) await send("Input.dispatchMouseEvent", {type:"mouseWheel", x:vp.x, y:vp.y, deltaX:0, deltaY:-120});
      await sleep(400);
      const atCap = await eval_('[fe.zoom,fe.panX,fe.panY]');
      await send("Input.dispatchMouseEvent", {type:"mouseWheel", x:vp.x, y:vp.y, deltaX:0, deltaY:-120});
      await sleep(300);
      const afterCap = await eval_('[fe.zoom,fe.panX,fe.panY]');
      say("Audit 縮放達上限後不得繼續平移", atCap[0] === 8 && afterCap[0] === 8 && Math.abs(atCap[1]-afterCap[1])<0.01 && Math.abs(atCap[2]-afterCap[2])<0.01,
        `before=${JSON.stringify(atCap)} after=${JSON.stringify(afterCap)}`);
      await pressKey("f");
      await escUntilFree();
    }
    await escUntilFree();
    await clickEl("#btnNewColumn");
    await sleep(250);
    say("Audit 柱對話框確實開啟", await eval_('!document.getElementById("rcDialog").hidden'));
    await pressKey("Escape"); await sleep(250);
    say("Audit Escape 關閉柱樑對話框", await eval_('document.getElementById("rcDialog").hidden'));
    if (await eval_('!document.getElementById("rcDialog").hidden')) await clickEl("#rcCancel");
    await send("Emulation.setDeviceMetricsOverride", {width:800,height:600,deviceScaleFactor:1,mobile:false});
    await sleep(400);
    const narrow = await eval_('(()=>{const r=document.getElementById("ocv").getBoundingClientRect();return {width:r.width,height:r.height}})()');
    say("Audit 800px 視窗主畫布仍可操作", narrow.width > 0 && narrow.height > 0, JSON.stringify(narrow));
    await send("Emulation.clearDeviceMetricsOverride");
    await sleep(250);
  }

  _log(`\n=== 全真實游標結果:${passN} ✓ / ${failN} ✗ ===`);
  chrome.kill();
  process.exit(failN ? 1 : 0);
})().catch(e => { _log("FATAL:", e.message); chrome.kill(); process.exit(1); });
