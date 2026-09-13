/* 畫布功能端到端測試：透過 serve.py 的 /api HTTP 介面（或直連 bridge）。
 * 用法：node canvas_test.js          → 走 http://localhost:8765/api
 *       node canvas_test.js direct   → 直接 spawn web_bridge.exe
 * 不重實作幾何——照抄前端的仿射/編輯算式，對照 bridge 的 uv/proj/bhit。
 */
const { spawn } = require("child_process");

const DIRECT = process.argv.includes("direct");
let api;
if (DIRECT) {
  const bridge = spawn(`"${__dirname.replace(/\//g, "\\")}\\web_bridge.exe"`,
                       [], { shell: true });
  let buf = "";
  const resolveQ = [];
  bridge.stdout.on("data", d => {
    buf += d;
    let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i); buf = buf.slice(i + 1);
      try { (resolveQ.shift() || (()=>{}))(JSON.parse(line)); }
      catch (e) { console.log("BAD JSON:", line); }
    }
  });
  api = cmd => { bridge.stdin.write(cmd + "\n");
                 return new Promise(r => resolveQ.push(r)); };
  process.on("exit", () => bridge.kill());
} else {
  api = cmd => fetch("http://localhost:8765/api", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cmd })
  }).then(r => r.json());
}

/* --- 抄自 index.html 的算式 --- */
async function uvMapFor(v, sid) {
  const [p00, p10, p01] = await Promise.all([
    api(`proj ${v} 0 0 ${sid}`), api(`proj ${v} 1000 0 ${sid}`), api(`proj ${v} 0 1000 ${sid}`)
  ]);
  if (!p00.ok || !p10.ok || !p01.ok) return null;
  const m = { ox: p00.x, oy: p00.y,
    ax: (p10.x - p00.x) / 1000, ay: (p10.y - p00.y) / 1000,
    bx: (p01.x - p00.x) / 1000, by: (p01.y - p00.y) / 1000 };
  m.det = m.ax * m.by - m.ay * m.bx;
  return m.det ? m : null;
}
const mapUv = (m,u,v) => ({ x: m.ox + u*m.ax + v*m.bx, y: m.oy + u*m.ay + v*m.by });
const unmapView = (m,x,y) => {
  const dx = x - m.ox, dy = y - m.oy;
  return { u: Math.round((dx*m.by - m.bx*dy)/m.det),
           v: Math.round((m.ax*dy - dx*m.ay)/m.det) };
};
const vertsStr = pts => pts.map(p => `${p[0]},${p[1]}`).join(" ");
function applyVertexEdit(pts, i, uv) {
  const n = pts.length, prev = pts[(i-1+n)%n], next = pts[(i+1)%n], cur = pts[i];
  if (prev[1] === cur[1]) prev[1] = uv.v; else prev[0] = uv.u;
  if (next[0] === cur[0]) next[0] = uv.u; else next[1] = uv.v;
  cur[0] = uv.u; cur[1] = uv.v;
}
function applyEdgeEdit(pts, i, uv) {
  const a = pts[i], b = pts[(i+1)%pts.length];
  if (a[1] === b[1]) { a[1] = b[1] = uv.v; } else { a[0] = b[0] = uv.u; }
}

let pass = 0, fail = 0;
function check(name, cond, detail="") {
  if (cond) { pass++; console.log("  PASS", name); }
  else { fail++; console.log("  FAIL", name, detail); }
}

(async () => {
  /* A. 新平面拉矩形(模擬:isNew + view 2 恆等映射) */
  console.log("== A. 新平面拉矩形 ==");
  await api("reset");
  const ids = await api("newid");
  const nid = Math.max(ids.boundary, ids.placement);
  const r1 = await api(`line surface ${nid} origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000`);
  check("建立矩形面", r1.ok, JSON.stringify(r1));
  const sf = await api("surfaces");
  check("surfaces 列出新面", sf.ok && sf.surfaces.some(s => s.id === nid));

  /* B. 仿射映射:JS 解出的 map 與 bridge 的 uv/proj 一致 */
  console.log("== B. 仿射映射一致性 ==");
  const sid = nid;
  const m = await uvMapFor(2, sid);   /* 俯視圖 */
  check("uvMapFor 取得映射", !!m);
  for (const [u,v] of [[0,0],[1500,700],[4000,3000],[1,2999]]) {
    const pj = await api(`proj 2 ${u} ${v} ${sid}`);
    const mq = mapUv(m, u, v);
    check(`mapUv(${u},${v})==proj`, pj.ok && Math.abs(pj.x-mq.x)<1 && Math.abs(pj.y-mq.y)<1,
          `proj=(${pj.x},${pj.y}) map=(${mq.x},${mq.y})`);
    const uvq = await api(`uv 2 ${pj.x} ${pj.y} ${sid}`);
    const uq = unmapView(m, pj.x, pj.y);
    check(`unmapView 逆解`, uvq.ok && uvq.u === uq.u && uvq.v === uq.v,
          `uv=(${uvq.u},${uvq.v}) unmap=(${uq.u},${uq.v})`);
  }
  const mFront = await uvMapFor(0, sid);
  check("前視圖看不到水平面(det=0)", mFront === null);

  /* C. bhit 命中頂點與邊 */
  console.log("== C. bhit ==");
  const hv = await api(`bhit ${sid} 0 0 60`);
  check("頂點命中", hv.ok && hv.kind === "vertex" && hv.loop === -1 && hv.index === 0, JSON.stringify(hv));
  const he = await api(`bhit ${sid} 2000 0 60`);
  check("邊命中", he.ok && he.kind === "edge" && he.loop === -1 && he.index === 0, JSON.stringify(he));
  const hn = await api(`bhit ${sid} 2000 1500 60`);
  check("中央不命中", !hn.ok, JSON.stringify(hn));

  /* D. 編輯:頂點拉角(4000,3000 → 5000,3000) */
  console.log("== D. 編輯頂點 ==");
  const b1 = await api(`boundary ${sid}`);
  const loops = b1.loops.map(l => ({ verts: l.verts.map(p=>[...p]), fixity: [...l.fixity] }));
  applyVertexEdit(loops[0].verts, 2, { u: 5000, v: 3000 });
  check("拉角後仍正交", loops[0].verts[2].join()==="5000,3000" &&
        loops[0].verts[1].join()==="5000,0" && loops[0].verts[3].join()==="0,3000");
  let s = `boundary ${sid} outline ` + vertsStr(loops[0].verts);
  const re = await api("line " + s);
  check("重宣告成功", re.ok, JSON.stringify(re));
  const b2 = await api(`boundary ${sid}`);
  check("邊界已更新", b2.ok && b2.loops[0].verts[1][0] === 5000);

  /* E. 編輯:拖邊(上邊 v=0 → v=200) */
  console.log("== E. 拖邊 ==");
  const b3 = await api(`boundary ${sid}`);
  const loops3 = b3.loops.map(l => ({ verts: l.verts.map(p=>[...p]), fixity: [...l.fixity] }));
  applyEdgeEdit(loops3[0].verts, 0, { u: 0, v: 200 });
  const re3 = await api(`line boundary ${sid} outline ` + vertsStr(loops3[0].verts));
  check("拖邊重宣告", re3.ok, JSON.stringify(re3));
  const b4 = await api(`boundary ${sid}`);
  check("邊已平移", b4.ok && b4.loops[0].verts[0].join()==="0,200" && b4.loops[0].verts[1].join()==="5000,200");

  /* F. 挖孔:矩形併入邊界重宣告 */
  console.log("== F. 挖孔 ==");
  const b5 = await api(`boundary ${sid}`);
  b5.loops.push({ verts: [[1000,1000],[2000,1000],[2000,2000],[1000,2000]], fixity: [1,1,1,1] });
  let sb = `boundary ${sid} outline ` + vertsStr(b5.loops[0].verts);
  for (let i = 1; i < b5.loops.length; ++i) sb += " hole " + vertsStr(b5.loops[i].verts);
  const re5 = await api("line " + sb);
  check("挖孔重宣告", re5.ok, JSON.stringify(re5));
  const b6 = await api(`boundary ${sid}`);
  check("孔已在", b6.ok && b6.loops.length === 2);
  const hh = await api(`bhit ${sid} 1000 1500 60`);
  check("孔邊可命中", hh.ok && hh.kind === "edge" && hh.loop === 0, JSON.stringify(hh));

  /* G. 非法輸入拒絕 */
  console.log("== G. 拒絕非法 ==");
  const g1 = await api(`line surface 9 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 500,1500 0,3000`);
  check("非正交拒絕", !g1.ok);
  const g2 = await api(`line surface 9 origin 0 0 0 u +x v +y outline 0,0 4000,0 2000,0 2000,3000 4000,3000`);
  check("自交拒絕", !g2.ok);
  const g3 = await api(`line boundary ${sid} outline 0,200 5000,200 5000,3000 0,3000 hole -50,0 100,0 100,100 -50,100`);
  check("越界孔拒絕", !g3.ok);
  const b7 = await api(`boundary ${sid}`);
  check("拒絕後邊界未變", b7.ok && b7.loops.length === 2);

  /* H. dump round-trip + 凍結錨點 */
  console.log("== H. dump round-trip ==");
  const d = await api("dump");
  check("dump 有內容", d.ok && d.text.includes("boundary"));
  check("dump 的 place 一律凍結 at u v", !/at-grid|at-edge|at-guides|through/.test(d.text));
  /* 重放 */
  await api("reset");
  for (const ln of d.text.split("\n").filter(l => l.trim())) {
    const rr = await api("line " + ln);
    if (!rr.ok) { check("重放: " + ln, false, JSON.stringify(rr)); }
  }
  const d2 = await api("dump");
  check("重放後 dump 相同", d2.ok && d2.text === d.text,
        "\n---原---\n" + d.text + "\n---重放---\n" + (d2.text||""));

  /* I. dump 凍結保真：at-grid 放角材後移動格線,dump 必須仍重放同一位置 */
  console.log("== I. 凍結保真 ==");
  await api("reset");
  const setup = [
    "line surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
    "line grid 1 on 1 u 2000",
    "line timber 1 27 33",
    "line place 1 on 1 at-grid 1 u 0 +v +n",
    "line grid 1 on 1 u 1500"          /* 移動參考線 → 凍結角材不該跟著走 */
  ];
  for (const ln of setup) await api(ln);
  const d3 = await api("dump");
  check("dump 後 place 是 at u v", d3.ok && /place 1 on 1 at \d+ \d+/.test(d3.text), d3.text);
  await api("reset");
  let replayOk = true;
  for (const ln of d3.text.split("\n").filter(l => l.trim())) {
    const rr = await api("line " + ln);
    if (!rr.ok) replayOk = false;
  }
  check("凍結 dump 可重放", replayOk);
  const d4 = await api("dump");
  check("凍結 dump round-trip 相同", d4.ok && d4.text === d3.text,
        "\n---原---\n" + d3.text + "\n---重放---\n" + (d4.text||""));

  console.log("== J. 物件畫布層 ==");
  await api("line reset");
  check("建游離面(無承載面)",
        (await api("line boundary 10 outline 0,0 400,0 400,300 0,300")).ok);
  check("建空容器空間", (await api("line space 9")).ok);
  check("canvas-pos 面", (await api("line canvas-pos boundary 10 120 80")).ok);
  check("canvas-pos 空間", (await api("line canvas-pos space 9 500 60")).ok);
  const ob = await api("objects");
  check("objects 列游離面",
        ob.ok && ob.faces.some(f => f.id === 10 && !f.placed));
  check("objects 列空容器",
        ob.ok && ob.spaces.some(s => s.id === 9 && s.members.length === 0 && !s.closed));
  const f10 = ob.faces.find(f => f.id === 10);
  check("objects 帶畫布座標", f10 && f10.hasPos && f10.cx === 120 && f10.cy === 80,
        JSON.stringify(f10));
  check("canvas-pos 壞目標被拒",
        !(await api("line canvas-pos boundary 999 0 0")).ok);
  check("canvas-pos 壞類別被拒",
        !(await api("line canvas-pos foo 10 0 0")).ok);
  check("放置游離面",
        (await api("line placement 10 on boundary 10 origin 0 0 0 u +x v +y")).ok);
  check("面入空間(重宣告)", (await api("line space 9 boundary 10")).ok);
  const ob2 = await api("objects");
  check("空間成員可見", ob2.ok && ob2.spaces[0].members.includes(10));
  const dA = (await api("dump")).text;
  check("dump 含 canvas-pos 與空間",
        /canvas-pos boundary 10 120 80/.test(dA) && /canvas-pos space 9/.test(dA)
        && /space 9 boundary 10/.test(dA), dA);
  await api("line reset");
  let replayOk2 = true;
  for (const l of dA.trim().split("\n")) {
    if (!(await api("line " + l)).ok) replayOk2 = false;
  }
  check("物件層 dump 可重放", replayOk2);
  const dB = (await api("dump")).text;
  check("物件層 round-trip 相同", dA === dB, "\n---原---\n" + dA + "\n---重放---\n" + dB);
  /* K. RC 柱/樑(B-2):建立、z/top 推導、拒絕路徑、delete 脫鉤、round-trip */
  console.log("== K. RC 柱/樑 ==");
  await api("line reset");
  const room = [
    "boundary 1 outline 0,0 4000,0 4000,3000 0,3000",
    "placement 1 on boundary 1 origin 0 0 2500 u +x v +y",   /* 天花 +Z */
    "boundary 2 outline 0,0 3000,0 3000,4000 0,4000",
    "placement 2 on boundary 2 origin 0 0 0 u +y v +x",      /* 地板 -Z */
    "boundary 3 outline 0,0 4000,0 4000,2500 0,2500",
    "placement 3 on boundary 3 origin 0 0 0 u +x v +z",      /* 牆 y=0 -Y */
    "boundary 4 outline 0,0 2500,0 2500,4000 0,4000",
    "placement 4 on boundary 4 origin 0 3000 0 u +z v +x",   /* 牆 y=3000 +Y */
    "boundary 5 outline 0,0 2500,0 2500,3000 0,3000",
    "placement 5 on boundary 5 origin 0 0 0 u +z v +y",      /* 牆 x=0 -X */
    "boundary 6 outline 0,0 3000,0 3000,2500 0,2500",
    "placement 6 on boundary 6 origin 4000 0 0 u +y v +z",   /* 牆 x=4000 +X */
    "space 1 boundary 1 2 3 4 5 6",
  ];
  let roomOk = true;
  for (const ln of room) if (!(await api("line " + ln)).ok) roomOk = false;
  check("六面盒空間", roomOk);
  const nidK = await api("newid");
  check("newid 含 column/beam", nidK.column >= 1 && nidK.beam >= 1);
  check("柱 z 推導成功",
        (await api(`line column ${nidK.column} in 1 at 1000 800 size 500 500`)).ok);
  const dK1 = (await api("dump")).text;
  check("推導 z=0~2500 寫進 dump", /column \d+ in 1 at 1000 800 size 500 500 z 0 2500/.test(dK1), dK1);
  check("樑 top 推導成功",
        (await api(`line beam ${nidK.beam} in 1 along x from 0 to 4000 at 1500 width 300 depth 500`)).ok);
  const dK2 = (await api("dump")).text;
  check("推導 top=2500 寫進 dump", /beam \d+ in 1 along x from 0 to 4000 at 1500 width 300 depth 500 top 2500/.test(dK2), dK2);
  check("游離柱無 z 拒絕", !(await api("line column 90 at 5000 5000 size 400 400")).ok);
  check("游離柱明寫 z 成立", (await api("line column 90 at 5000 5000 size 400 400 z 0 2600")).ok);
  check("游離樑無 top 拒絕", !(await api("line beam 90 along x from 0 to 1000 at 500 width 300 depth 500")).ok);
  check("游離樑明寫 top 成立", (await api("line beam 90 along x from 0 to 1000 at 500 width 300 depth 500 top 2600")).ok);
  check("柱-柱重疊拒絕", !(await api("line column 91 in 1 at 1100 900 size 500 500")).ok);
  check("柱足跡越界拒絕", !(await api("line column 91 in 1 at 3800 2800 size 500 500")).ok);
  check("樑非法軸拒絕", !(await api("line beam 91 in 1 along z from 0 to 100 at 100 width 300 depth 500")).ok);
  check("in 不存在空間拒絕", !(await api("line column 92 in 99 at 100 100 size 300 300")).ok);
  const obK = await api("objects");
  check("objects 列柱樑",
        obK.ok && obK.columns.length === 2 && obK.beams.length === 2 &&
        obK.columns[0].box.length === 6, JSON.stringify(obK.columns));
  check("canvas-pos 柱", (await api(`line canvas-pos column ${nidK.column} 700 60`)).ok);
  check("canvas-pos 樑", (await api(`line canvas-pos beam ${nidK.beam} 900 60`)).ok);
  const obK2 = await api("objects");
  const colK = obK2.columns.find(c => c.id === nidK.column);
  check("柱卡座標落地", colK && colK.hasPos && colK.cx === 700, JSON.stringify(colK));
  /* 三視圖 render:柱/樑的投影矩形要出現在 ops(style 13/14) */
  const rdK = await api("render");
  const rcOps = (rdK.ops || []).filter(o => o.s === 13 || o.s === 14);
  check("三視圖有柱/樑投影", rcOps.length >= 2, `rc ops=${rcOps.length}`);
  /* delete 語意 */
  check("刪柱", (await api(`line delete column ${nidK.column}`)).ok);
  const obK3 = await api("objects");
  check("刪後柱消失", obK3.columns.length === 1);
  check("刪空間→柱樑脫鉤", (await api("line delete space 1")).ok);
  const dK3 = (await api("dump")).text;
  check("脫鉤後柱變游離", /column 90 at 5000 5000/.test(dK3) && !/column \d+ in 1 /.test(dK3), dK3);
  check("脫鉤後樑變游離", !/beam \d+ in 1 /.test(dK3), dK3);
  /* dump round-trip(含柱樑) */
  await api("line reset");
  let replayK = true;
  for (const l of dK3.trim().split("\n")) {
    if (!(await api("line " + l)).ok) replayK = false;
  }
  check("柱樑 dump 可重放", replayK);
  check("柱樑 round-trip 相同", (await api("dump")).text === dK3);

  /* ==== §L. obstacles 鬼影分類(R7 五種接觸,P12)==== */
  await api("line reset");
  let roomL = true;
  for (const ln of room) if (!(await api("line " + ln)).ok) roomL = false;
  check("L 六面盒重建", roomL);
  const mkL = async l => (await api("line " + l)).ok;
  check("L 獨立柱", await mkL("column 1 in 1 at 1000 1000 size 400 400"));
  check("L 貼牆柱", await mkL("column 2 in 1 at 0 1500 size 400 400"));
  check("L 角柱", await mkL("column 3 in 1 at 3600 2600 size 400 400"));
  check("L 搭牆樑", await mkL("beam 1 in 1 along y from 0 to 3000 at 2000 width 300 depth 500"));
  check("L 邊樑", await mkL("beam 2 in 1 along x from 0 to 4000 at 150 width 300 depth 400"));

  const obL1 = await api("obstacles 1");   /* 天花 +Z */
  const cls1 = Object.fromEntries((obL1.items || []).map(i => [i.type + i.id, i.cls]));
  check("天花:獨立柱→孔", cls1.column1 === "hole", JSON.stringify(cls1));
  check("天花:貼牆柱→凹口", cls1.column2 === "notch");
  check("天花:角柱→角凹", cls1.column3 === "corner");
  check("天花:搭牆樑→條帶", cls1.beam1 === "strip");
  check("天花:邊樑→條帶", cls1.beam2 === "strip");

  const obL2 = await api("obstacles 2");   /* 地板 -Z:樑不該出現 */
  const cls2 = Object.fromEntries((obL2.items || []).map(i => [i.type + i.id, i.cls]));
  check("地板:柱三分類", cls2.column1 === "hole" && cls2.column2 === "notch" &&
        cls2.column3 === "corner", JSON.stringify(cls2));
  check("地板:無樑影", !cls2.beam1 && !cls2.beam2);

  const obL3 = await api("obstacles 3");   /* 牆 y=0 -Y */
  const cls3 = Object.fromEntries((obL3.items || []).map(i => [i.type + i.id, i.cls]));
  check("牆:搭牆樑→頂凹", cls3.beam1 === "top_notch", JSON.stringify(cls3));
  check("牆:邊樑→頂降", cls3.beam2 === "top_drop");
  check("牆:柱2 不貼牆→無項", !cls3.column2);

  const obL5 = await api("obstacles 5");   /* 牆 x=0 -X:柱2 貼牆 → split */
  const cls5 = Object.fromEntries((obL5.items || []).map(i => [i.type + i.id, i.cls]));
  check("牆:貼牆柱→拆分", cls5.column2 === "split", JSON.stringify(cls5));
  check("牆:邊樑端搭→頂凹", cls5.beam2 === "top_notch");

  const obL6 = await api("obstacles 6");   /* 牆 x=4000 +X:柱3 角貼 → split */
  const cls6 = Object.fromEntries((obL6.items || []).map(i => [i.type + i.id, i.cls]));
  check("牆:角柱→拆分", cls6.column3 === "split", JSON.stringify(cls6));

  /* 鬼影不改 boundary:obstacles 前後 boundary 1 的輪廓要相同 */
  const bBefore = await api("boundary 1");
  await api("obstacles 1");
  const bAfter = await api("boundary 1");
  check("鬼影不改邊界", JSON.stringify(bBefore) === JSON.stringify(bAfter));
  /* 未放置面 → ok:false(R9) */
  check("未放置面拒絕", !(await api("line boundary 7 outline 0,0 100,0 100,100 0,100")).ok === false ||
        !(await api("obstacles 7")).ok);

  /* ==== §M. apply-proj 套用(P13:B-1 七種分類 + 拆分/回滾)==== */
  console.log("== M. apply-proj ==");
  const freshRoom = async () => {
    await api("line reset");
    let ok = true;
    for (const ln of room) if (!(await api("line " + ln)).ok) ok = false;
    for (const ln of [
      "column 1 in 1 at 1000 1000 size 400 400",
      "column 2 in 1 at 0 1500 size 400 400",
      "column 3 in 1 at 3600 2600 size 400 400",
      "beam 1 in 1 along y from 0 to 3000 at 2000 width 300 depth 500",
      "beam 2 in 1 along x from 0 to 4000 at 150 width 300 depth 400",
    ]) if (!(await api("line " + ln)).ok) ok = false;
    return ok;
  };
  check("M 六面盒+五夾具", await freshRoom());

  /* M1 天花柱孔(id 1 同時套柱1孔+樑1條帶;條帶未勾=不裁→外環不變) */
  check("M1 apply 柱孔", (await api("line apply-proj 1 1")).ok);
  const bM1 = await api("boundary 1");
  check("M1 孔進 boundary", bM1.ok && bM1.loops.length === 2 &&
        bM1.loops[1].verts.length === 4, JSON.stringify(bM1.loops));
  check("M1 條帶未裁:外環仍是 4 頂點",
        bM1.loops[0].verts.length === 4);
  check("M1 孔 fixity 全 F", bM1.loops[1].fixity.every(f => f));

  /* M2 角柱 → 角凹(4→6 頂點) */
  check("M2 apply 角柱", (await api("line apply-proj 1 3")).ok);
  const bM2 = await api("boundary 1");
  check("M2 外環 6 頂點", bM2.loops[0].verts.length === 6,
        JSON.stringify(bM2.loops[0].verts));

  /* M3 地板貼邊柱 → 凹口(4→8 頂點) */
  check("M3 apply 貼邊柱", (await api("line apply-proj 2 2")).ok);
  const bM3 = await api("boundary 2");
  check("M3 外環 8 頂點", bM3.loops[0].verts.length === 8,
        JSON.stringify(bM3.loops[0].verts));

  /* M4 貼牆柱 → 牆拆分(同時套樑2 頂凹):面變多、空間成員掉 5 */
  check("M4 apply 牆拆分", (await api("line apply-proj 5 2")).ok);
  const obM4 = await api("objects");
  check("M4 面數 6→8(拆片+柱側面)", obM4.faces.length === 8,
        `faces=${obM4.faces.length}`);
  const spM4 = obM4.spaces.find(s => s.id === 1);
  check("M4 空間成員剔除原牆", spM4 && !spM4.members.includes(5) &&
        spM4.members.length === 5, JSON.stringify(spM4 && spM4.members));
  const bM4 = await api("boundary 5");
  check("M4 原 id 留最大片", bM4.ok && bM4.loops[0].verts.length >= 4);
  /* dump 回讀 */
  const dM4 = (await api("dump")).text;
  await api("line reset");
  let rpM4 = true;
  for (const l of dM4.trim().split("\n"))
    if (!(await api("line " + l)).ok) rpM4 = false;
  check("M4 dump 可重放", rpM4);
  check("M4 round-trip 相同", (await api("dump")).text === dM4);

  /* M5 條帶裁切:天花拆兩片 + 樑底 + 樑兩側 = +4 面,孔重分配 */
  check("M5 重建", await freshRoom());
  check("M5 apply 柱孔先落", (await api("line apply-proj 1 c1")).ok);
  check("M5 重套同孔拒絕(快照)", !(await api("line apply-proj 1 c1")).ok);
  check("M5 apply cut-strip", (await api("line apply-proj 1 b1 cut-strip")).ok);
  const obM5 = await api("objects");
  check("M5 面數 6→10", obM5.faces.length === 10,
        `faces=${obM5.faces.length}`);
  const spM5 = obM5.spaces.find(s => s.id === 1);
  check("M5 天花退出空間", spM5 && !spM5.members.includes(1));
  /* 孔(在 u<1850 片)要跟著到新片,不該留在保留片 */
  const bM5 = await api("boundary 1");
  check("M5 保留片無孔", bM5.ok && bM5.loops.length === 1,
        JSON.stringify(bM5.loops && bM5.loops.length));
  const holePiece = obM5.faces.find(f => f.id !== 1 && f.id > 6);
  const bM5b = holePiece && await api(`boundary ${holePiece.id}`);
  check("M5 孔隨片走", bM5b && bM5b.loops && bM5b.loops.length === 2,
        JSON.stringify(holePiece));
  /* render 一致性:新片+樑面照常出 ops */
  const rdM5 = await api("render");
  check("M5 render 有面", (rdM5.ops || []).length > 0);

  /* M6 回滾:不存在的項目 id → 拒絕且世界不變 */
  const dPre = (await api("dump")).text;
  check("M6 壞 id 拒絕", !(await api("line apply-proj 1 99")).ok);
  check("M6 世界未變", (await api("dump")).text === dPre);
  /* M7 未放置面拒絕(R9) */
  check("M7 不存在面拒絕", !(await api("line apply-proj 20 1")).ok);
  check("M7 建未放置面", (await api("line boundary 20 outline 0,0 100,0 100,100 0,100")).ok);
  check("M7 未放置面拒絕(R9)", !(await api("line apply-proj 20 1")).ok);

  /* M8 拆分時承載面輔助資料跟著含錨點的那片走(R13):
     天花(u=x 0-4000, v=y 0-3000)被 x=2800±150 的樑條帶裁切 →
     保留片 u<2650(id 1 留最大片),新片 u>2950(新 id)。
     錨在新片的 guide/grid/timber 要改掛新承載面;
     錨在移除帶的 guide → 整筆拒絕回滾。 */
  check("M8 重建", await freshRoom());
  check("M8 建樑(x=2800)", (await api(
        "line beam 3 in 1 along y from 0 to 3000 at 2800 width 300 depth 500")).ok);
  let auxOk = true;
  for (const ln of [
    "guide 1 1 v 3500",        /* 固定 u=3500 → 只在新片 */
    "guide 2 1 u 1500",        /* 固定 v=1500 → 兩片都合法 → 留原片 */
    "grid 1 on 1 u 3500 v 1500",/* u 座標 3500 → 只在新片 */
    "timber 1 400 27 33",
    "place 1 on 1 at 3500 1500 +u +n",  /* 錨點 (3500,1500) → 新片 */
  ]) if (!(await api("line " + ln)).ok) { auxOk = false; console.log("  M8 aux fail:", ln); }
  check("M8 輔助資料就緒", auxOk);
  check("M8 apply cut-strip", (await api("line apply-proj 1 b3 cut-strip")).ok);
  const dM8 = (await api("dump")).text;
  check("M8 新片 guide 改掛", /guide 1 7 v 3500/.test(dM8), dM8);
  check("M8 兩棲 guide 留原片", /guide 2 1 u 1500/.test(dM8), dM8);
  check("M8 網格改掛新片", /grid 1 on 7/.test(dM8), dM8);
  check("M8 角材改掛新片", /place 1 on 7 at 3500 1500/.test(dM8), dM8);
  /* M8b 錨在移除帶(u=2800)的 guide → 整筆拒絕,世界不變 */
  check("M8b 重建", await freshRoom() &&
        (await api("line beam 3 in 1 along y from 0 to 3000 at 2800 width 300 depth 500")).ok &&
        (await api("line guide 1 1 v 2800")).ok);
  const dM8b = (await api("dump")).text;
  check("M8b 帶上錨點拒絕", !(await api("line apply-proj 1 b3 cut-strip")).ok);
  check("M8b 世界未變", (await api("dump")).text === dM8b);

  await api("default");

  console.log(`\n${pass} pass / ${fail} fail`);
  process.exit(fail ? 1 : 0);
})();
