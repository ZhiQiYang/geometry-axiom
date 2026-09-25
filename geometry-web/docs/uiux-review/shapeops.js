/* 正交多邊形的矩形布林運算（減／加）與邊、角查詢。純函式，無 DOM。 */
(function () {
  function pointInLoop(pt, loop) {
    let ins = false; const [x, y] = pt;
    for (let i = 0, j = loop.length - 1; i < loop.length; j = i++) {
      const [xi, yi] = loop[i], [xj, yj] = loop[j];
      if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) ins = !ins;
    }
    return ins;
  }
  function inside(loops, x, y) {
    if (!loops.length || !pointInLoop([x, y], loops[0])) return false;
    for (let k = 1; k < loops.length; k++) if (pointInLoop([x, y], loops[k])) return false;
    return true;
  }
  function area(loop) {
    let a = 0;
    for (let i = 0, j = loop.length - 1; i < loop.length; j = i++) a += loop[j][0] * loop[i][1] - loop[i][0] * loop[j][1];
    return a / 2;
  }
  function bbox(loops) {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    loops.forEach(l => l.forEach(([x, y]) => { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }));
    return [x0, y0, x1, y1];
  }
  function simplify(pts) {
    const out = pts.slice(); let changed = true;
    while (changed && out.length > 2) {
      changed = false;
      for (let i = 0; i < out.length; i++) {
        const p = out[(i - 1 + out.length) % out.length], c = out[i], n = out[(i + 1) % out.length];
        if ((p[0] === c[0] && c[0] === n[0]) || (p[1] === c[1] && c[1] === n[1]) || (c[0] === n[0] && c[1] === n[1])) { out.splice(i, 1); changed = true; break; }
      }
    }
    return out;
  }
  /* loops: [outer, ...holes]；op 'sub'|'add'；rect [x0,y0,x1,y1] → {loops, split} 或 null */
  function applyRect(loops, op, r) {
    const x0 = Math.min(r[0], r[2]), x1 = Math.max(r[0], r[2]), y0 = Math.min(r[1], r[3]), y1 = Math.max(r[1], r[3]);
    if (x1 - x0 < 1e-6 || y1 - y0 < 1e-6) return null;
    const xs = new Set([x0, x1]), ys = new Set([y0, y1]);
    loops.forEach(l => l.forEach(([x, y]) => { xs.add(x); ys.add(y); }));
    const X = [...xs].sort((a, b) => a - b), Y = [...ys].sort((a, b) => a - b);
    const nx = X.length - 1, ny = Y.length - 1, F = new Uint8Array(nx * ny);
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
      const cx = (X[i] + X[i + 1]) / 2, cy = (Y[j] + Y[j + 1]) / 2;
      const ins = inside(loops, cx, cy), inR = cx > x0 && cx < x1 && cy > y0 && cy < y1;
      F[j * nx + i] = (op === "sub" ? (ins && !inR) : (ins || inR)) ? 1 : 0;
    }
    const get = (i, j) => (i < 0 || j < 0 || i >= nx || j >= ny) ? 0 : F[j * nx + i];
    const segs = new Map(), key = (x, y) => x + "," + y;
    const add = (a, b) => { const k = key(a[0], a[1]); if (!segs.has(k)) segs.set(k, []); segs.get(k).push(b); };
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
      if (!F[j * nx + i]) continue;
      const a = [X[i], Y[j]], b = [X[i + 1], Y[j]], c = [X[i + 1], Y[j + 1]], d = [X[i], Y[j + 1]];
      if (!get(i, j - 1)) add(a, b); if (!get(i + 1, j)) add(b, c); if (!get(i, j + 1)) add(c, d); if (!get(i - 1, j)) add(d, a);
    }
    const out = [];
    while (segs.size) {
      const k0 = segs.keys().next().value, start = k0.split(",").map(Number);
      let cur = start; const pts = []; let guard = 0;
      while (guard++ < 100000) {
        pts.push(cur);
        const k = key(cur[0], cur[1]), arr = segs.get(k);
        if (!arr || !arr.length) break;
        const nxt = arr.shift(); if (!arr.length) segs.delete(k);
        cur = nxt;
        if (cur[0] === start[0] && cur[1] === start[1]) break;
      }
      const s = simplify(pts); if (s.length >= 4) out.push(s);
    }
    if (!out.length) return null;
    out.sort((a, b) => Math.abs(area(b)) - Math.abs(area(a)));
    const outer = out[0], so = Math.sign(area(outer));
    const holes = out.slice(1).filter(l => Math.sign(area(l)) !== so);
    return { loops: [outer, ...holes], split: out.length - 1 - holes.length > 0 };
  }
  /* 外環的邊：axis 'h'|'v'、固定座標 c、範圓 lo..hi、outSign = 向外的方向（該軸正負） */
  function edges(loop) {
    const n = loop.length, res = [];
    for (let i = 0; i < n; i++) {
      const p0 = loop[i], p1 = loop[(i + 1) % n];
      const axis = p0[1] === p1[1] ? "h" : "v";
      const c = axis === "h" ? p0[1] : p0[0];
      const a0 = axis === "h" ? p0[0] : p0[1], a1 = axis === "h" ? p1[0] : p1[1];
      const lo = Math.min(a0, a1), hi = Math.max(a0, a1), mid = (lo + hi) / 2;
      const tx = axis === "h" ? mid : c + 0.5, ty = axis === "h" ? c + 0.5 : mid;
      const outSign = pointInLoop([tx, ty], loop) ? -1 : 1;
      res.push({ i, p0, p1, axis, c, lo, hi, len: hi - lo, outSign });
    }
    return res;
  }
  /* 外環的角：sx/sy = 從角往面內走的方向；convex = 凸角 */
  function corners(loop) {
    const n = loop.length, res = [];
    for (let i = 0; i < n; i++) {
      const v = loop[i], p = loop[(i - 1 + n) % n], q = loop[(i + 1) % n];
      const hn = p[1] === v[1] ? p : q, vn = hn === p ? q : p;
      const sx = Math.sign(hn[0] - v[0]) || 1, sy = Math.sign(vn[1] - v[1]) || 1;
      const convex = pointInLoop([v[0] + sx * 0.5, v[1] + sy * 0.5], loop);
      res.push({ i, v, sx, sy, convex });
    }
    return res;
  }
  /* 邊上矩形：anchor 'start'|'center'|'end'（沿軸正向起算）、dist、w（沿邊）、d（深）、dir 'in'|'out' */
  function edgeRect(e, o) {
    const w = Math.max(0, o.w), d = Math.max(0, o.d);
    let s = o.anchor === "end" ? e.hi - o.dist - w : o.anchor === "center" ? e.lo + (e.len - w) / 2 : e.lo + o.dist;
    const sign = o.dir === "out" ? e.outSign : -e.outSign, c2 = e.c + sign * d;
    return e.axis === "h" ? [s, Math.min(e.c, c2), s + w, Math.max(e.c, c2)] : [Math.min(e.c, c2), s, Math.max(e.c, c2), s + w];
  }
  window.ShapeOps = { pointInLoop, inside, area, bbox, applyRect, edges, corners, edgeRect };
})();
