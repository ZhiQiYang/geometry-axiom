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
  await api("default");

  console.log(`\n${pass} pass / ${fail} fail`);
  process.exit(fail ? 1 : 0);
})();
