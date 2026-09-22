/*
 * polydraft.js — 「面·多邊形逐點閉合(正交)」共用草稿狀態機
 *
 * 純邏輯模組:不碰 DOM、不送 bridge(不呼叫 api/emitLine/emitBoundary,不 import/require
 * 任何 DOM API),所有輸入輸出都是 plain object/array。供主畫布 P 工具與面內「重畫外環」e
 * 兩處呼叫端共用同一份狀態機,由各自呼叫端決定 gridMm/snapOn/zoom 等策略參數。
 *
 * 介面 SSOT:geometry-web/docs/POLYDRAFT-API.md(狀態形狀、函式簽名、錯誤碼)。
 * 行為規格:geometry-web/docs/RC-POLYGON-PLAN.md §5.A.1。
 *
 * 座標系:所有 pt/pts 一律是呼叫端已換算好的 scene 座標(整數 mm);螢幕像素閾值
 * (±8px 對齊、12px 閉合半徑)由呼叫端傳入 zoom,本模組內部除以 zoom 換成 scene 距離。
 *
 * ================================================================
 * 閉合驗證的設計原則(GEO-178,請先讀完再改這個檔)
 * ================================================================
 * 連續三輪對抗審查(F1/F2、G1、G3/G4)找到的其實是同一個根源的四個出口:
 * 「有些新邊沒走檢查」與「拿化簡後的形狀去判合法」。以下三條是原則,不是補丁——
 * 任何新的落點/收尾管道都要照這三條接上去,不要再對個別案例加 gate。
 *
 * 原則 1:草稿折線不變式(增量維持)
 *   任何時刻,已定頂點 pts 構成的折線都滿足:每邊軸平行且非零長、相鄰兩邊互相垂直
 *   (共線同向在落點當下就併成一條邊、共線反向一律拒絕 = BACKTRACK)、非相鄰邊完全
 *   不接觸(端點觸碰也算)、且不接觸呼叫端給的 existingEdges。
 *   **所有**會動到 pts 的管道都必須走 evaluateNextPoint 才准改 pts:place、
 *   applyTypedLength(GEO-178 之前它完全不檢查,是 G3 唯一能打穿的管道 = G4 根因)。
 *
 * 原則 2:閉合 = 對「raw 環」做一次總驗證(evaluateClosedRing → ringGeometryError)
 *   tryClose 把閉合段(直接閉合 L→F;補角 L→C、C→F)接上去之後,對**還沒去共線的
 *   原始點列**跑 ringGeometryError——它逐條對齊 current_geometry.c::poly_loop_is_valid
 *   (每邊軸平行非零長、非相鄰邊不得相交或共線重疊,含「首邊與末邊相鄰」的排除),
 *   另加一條核心沒明寫、但化簡要求的相鄰邊規則:相鄰兩邊只准共享那一個端點,共線同側
 *   (兩段實際疊在一起)一律非法。這道總驗證涵蓋了「每一段新邊都要被檢查」(新段對
 *   草稿自身所有已定邊 + existingEdges),而且是對 raw 幾何做的——絕不可以拿去共線
 *   後的點列判合法:G3 就是這樣被放行的(raw 5 點 core.exe 拒絕、deduped 4 點 core.exe
 *   接受,模組拿後者當通行證,靜默送出一個使用者沒畫的矩形)。
 *
 * 原則 3:去共線只是輸出前的化簡,不承擔任何「判合法」責任
 *   dedupeLoop 只在原則 2 通過之後才跑,用途是拿掉共線贅點(收尾段與首段/末段共線時,
 *   F 或 L 會變成沒有轉彎的贅點)。因為原則 2 已保證環是簡單多邊形,化簡至多只會拿掉
 *   落在輸出多邊形邊上的贅點,形狀恆等:shoelace 面積相等、raw 每個頂點都落在輸出
 *   多邊形的邊上、輸出每個頂點都是 raw 頂點(polydraft_test.js 的 assertShapePreserved
 *   把這條寫成通用斷言,套在全部手寫與隨機案例上——這就是擋 G3 那類「形狀被化簡偷改」
 *   的牙)。唯一排在原則 2 前面的檢查是「化簡後湊不齊 4 個頂點」→ TOO_FEW:那代表
 *   形狀根本還沒成形,比自交更前置(三點共線的草稿該回 TOO_FEW,而不是答非所問的 CROSS)。
 */
"use strict";

/* ---------------------------------------------------------------- */
/* 內部工具:軸平行線段相交/共線重疊判定(含端點觸碰),風格對齊
   current_geometry.c 的 poly_loop_is_valid——非相鄰邊「觸碰即視為相交」。 */
/* ---------------------------------------------------------------- */

/* 核心頂點上限的鏡射(GEO-179)。來源 current_geometry.c(此檔統一 CRLF,用二進位讀):
     :198      #define POLY_MAX_VERTICES 32
     :229-232  poly_loop_is_valid:count < 4 或 count > POLY_MAX_VERTICES → 不合法
     :8487-8489 parse_loop_vertices:場景 DSL 讀到第 33 個 u,v 直接 return -1,
                呼叫端(:8568-8574)報「outline 後面要接至少四個 u,v 頂點」——同一句話
                兼管太少與太多,所以核心的拒絕訊息分不出這兩者,前端必須自己講清楚。
   這是鏡射不是猜測:polydraft_test.js 的「跨層裁判(GEO-179)」實跑 core.exe 對 32/33/34
   點 outline 各驗一次(ACCEPT/REJECT/REJECT),核心真的換了上限那個測試會紅。 */
const POLY_MAX_VERTICES = 32;
const TOO_MANY_MSG = `外環最多 ${POLY_MAX_VERTICES} 個頂點`;

/* 核心座標範圍的鏡射(GEO-180,對抗審查 H1)。來源 current_geometry.c:
     :43       #define COORD_LIMIT INT64_C(100000000)   (±100 km,單位 mm)
     :44-47    coord_in_range(v) = (v >= -COORD_LIMIT && v <= COORD_LIMIT)
               → **兩端都含等號**,±1e8 本身合法,超過一單位才非法
     :239      poly_loop_is_valid 對環上**每一個頂點**的 u/v 各驗一次
     :12026    場景 DSL 另有一道:「座標或尺寸超出支援範圍(-100000000 至 100000000 mm)」
   同樣是鏡射不是猜測:polydraft_test.js 的「跨層裁判(GEO-180)」用 core.exe 實測
   ±1e8 → ACCEPT、±(1e8+1) → REJECT 把邊界釘住,核心改範圍那個測試會紅。 */
const COORD_LIMIT = 100000000;
const OUT_OF_RANGE_MSG = `座標超出支援範圍(±${COORD_LIMIT} mm)`;

function coordInRange(v) { return v >= -COORD_LIMIT && v <= COORD_LIMIT; }
function pointInRange(p) { return coordInRange(p[0]) && coordInRange(p[1]); }

function segmentsIntersect(segA, segB) {
  const a1 = segA[0], a2 = segA[1], b1 = segB[0], b2 = segB[1];
  const aVert = a1[0] === a2[0];
  const bVert = b1[0] === b2[0];

  if (aVert && bVert) {
    /* 兩條直立邊 */
    if (a1[0] !== b1[0]) return false;
    const aMin = Math.min(a1[1], a2[1]), aMax = Math.max(a1[1], a2[1]);
    const bMin = Math.min(b1[1], b2[1]), bMax = Math.max(b1[1], b2[1]);
    return Math.max(aMin, bMin) <= Math.min(aMax, bMax);
  }

  const aHoriz = a1[1] === a2[1];
  const bHoriz = b1[1] === b2[1];
  if (aHoriz && bHoriz) {
    /* 兩條水平邊 */
    if (a1[1] !== b1[1]) return false;
    const aMin = Math.min(a1[0], a2[0]), aMax = Math.max(a1[0], a2[0]);
    const bMin = Math.min(b1[0], b2[0]), bMax = Math.max(b1[0], b2[0]);
    return Math.max(aMin, bMin) <= Math.min(aMax, bMax);
  }

  /* 一橫一直:交點須同時落在兩邊的範圍內(含端點) */
  let h1, h2, s1, s2;
  if (aHoriz) { h1 = a1; h2 = a2; s1 = b1; s2 = b2; }
  else { h1 = b1; h2 = b2; s1 = a1; s2 = a2; }
  const huMin = Math.min(h1[0], h2[0]), huMax = Math.max(h1[0], h2[0]);
  const svMin = Math.min(s1[1], s2[1]), svMax = Math.max(s1[1], s2[1]);
  return s1[0] >= huMin && s1[0] <= huMax && h1[1] >= svMin && h1[1] <= svMax;
}

function samePoint(a, b) { return a[0] === b[0] && a[1] === b[1]; }

/* 共享一個端點的兩條軸平行段,彼此是什麼關係——原則 1(落點)與原則 2(收尾)共用的
   唯一判準,不要各寫一份:
     "perpendicular"     互相垂直,只共享那一點 → 合法
     "collinear-through" 共線但往相反側延伸,仍然只共享那一點 → 合法;shared 是一個
                         沒有轉彎的共線贅點,落點時就地合併、收尾時交給 dedupeLoop
                         化簡掉(兩者都不改變形狀)
     "overlap"           共線且往同一側,兩段實際疊在一起 → 非法(落點時是 BACKTRACK;
                         收尾時是「收尾段壓在首段/末段上」,化簡會把形狀改掉)
   呼叫前必須先排除零長(shared 與 otherA/otherB 重合),否則 Math.sign 會取到 0。 */
function adjacencyRelation(shared, otherA, otherB) {
  if (otherA[0] === shared[0] && otherB[0] === shared[0]) {
    return Math.sign(otherA[1] - shared[1]) === Math.sign(otherB[1] - shared[1])
      ? "overlap" : "collinear-through";
  }
  if (otherA[1] === shared[1] && otherB[1] === shared[1]) {
    return Math.sign(otherA[0] - shared[0]) === Math.sign(otherB[0] - shared[0])
      ? "overlap" : "collinear-through";
  }
  return "perpendicular";
}

/* 原則 2 的本體:對一條「raw(未去共線)封閉環」做合法性總驗證。
   回傳 null(合法)或 { kind, at }(供除錯;呼叫端只看有沒有)。
   規則逐條對齊 current_geometry.c::poly_loop_is_valid(約 :227-310):
     ① 每邊軸平行且非零長。
     ② 非相鄰邊不得相交或共線重疊(觸碰即算),含「i===0 且 j+1===n」的首末邊排除
        ——首邊與末邊相鄰,共享頂點合法。
     ③(核心沒明寫、但化簡要求)相鄰兩邊只准共享那一個端點:共線同側=兩段疊在一起,
        核心是靠旁邊那條邊被 ② 抓到才間接拒絕,本模組直接寫明,免得化簡把形狀改掉。
   頂點數與面積不在這裡判(分別是 TOO_FEW/DEGENERATE 的職責,見 evaluateClosedRing)。 */
function ringGeometryError(ring) {
  const n = ring.length;
  if (n < 3) return { kind: "TOO_SHORT", at: n };

  for (let i = 0; i < n; ++i) {
    const a = ring[i], b = ring[(i + 1) % n];
    if (samePoint(a, b)) return { kind: "ZERO_EDGE", at: i };
    if (a[0] !== b[0] && a[1] !== b[1]) return { kind: "NOT_AXIS_PARALLEL", at: i };
  }

  for (let i = 0; i < n; ++i) {
    const prev = ring[i], shared = ring[(i + 1) % n], next = ring[(i + 2) % n];
    if (adjacencyRelation(shared, prev, next) === "overlap") {
      return { kind: "ADJACENT_OVERLAP", at: i };
    }
  }

  for (let i = 0; i < n; ++i) {
    const a1 = ring[i], a2 = ring[(i + 1) % n];
    for (let j = i + 2; j < n; ++j) {
      if (i === 0 && j + 1 === n) continue;   /* 首邊與末邊相鄰,共享頂點合法 */
      const b1 = ring[j], b2 = ring[(j + 1) % n];
      if (segmentsIntersect([a1, a2], [b1, b2])) {
        return { kind: "NON_ADJACENT_TOUCH", at: [i, j] };
      }
    }
  }
  return null;
}

/* 去共線(等同既有 feDedupe):前後兩點都與中間點同 x 或同 y 就丟棄該點。
   pts 視為封閉環(wraparound),以原陣列的鄰居判斷(不因刪除而位移)。 */
function dropCollinear(ring) {
  const n = ring.length;
  const out = [];
  for (let i = 0; i < n; ++i) {
    const a = ring[(i - 1 + n) % n], b = ring[i], c = ring[(i + 1) % n];
    if ((a[0] === b[0] && b[0] === c[0]) || (a[1] === b[1] && b[1] === c[1])) continue;
    out.push(b);
  }
  return out;
}

/* 合併相鄰重合點(含首尾繞回的那一對)。 */
function mergeCoincident(ring) {
  const out = [];
  for (const p of ring) {
    const prev = out[out.length - 1];
    if (prev && samePoint(prev, p)) continue;
    out.push(p);
  }
  while (out.length > 1 && samePoint(out[0], out[out.length - 1])) out.pop();
  return out;
}

/* 原則 3:輸出前的化簡。先合併重合、再去共線,迭代到穩定(單一 pass 對「重合點與
   共線贅點交錯」的退化輸入不穩健)。它**不判合法**——合法性在 ringGeometryError;
   環已是簡單多邊形時,這裡至多只拿掉落在輸出邊上的共線贅點,形狀恆等。 */
function dedupeLoop(pts) {
  let cur = pts.slice();
  for (let guard = 0; guard < 64 && cur.length > 0; ++guard) {
    const next = dropCollinear(mergeCoincident(cur));
    if (next.length === cur.length) return next;   /* 只減不增:長度沒變 = 已穩定 */
    cur = next;
  }
  return cur;
}

/* shoelace 有向面積的兩倍(整數運算,不會有浮點誤差)。 */
function ringArea2(ring) {
  let area2 = 0;
  for (let i = 0; i < ring.length; ++i) {
    const a = ring[i], b = ring[(i + 1) % ring.length];
    area2 += a[0] * b[1] - b[0] * a[1];
  }
  return area2;
}

/* 原則 1 的本體:判斷「從 pts 最後一點畫向 candidate」這一段的結果:
   - duplicate:candidate 與末點重合,呼叫端應忽略(不落點、不算錯誤)
   - error:BACKTRACK(與最後一段共線同側=疊在一起)或 CROSS(與既有邊/自身較早的邊接觸)
   - extend:candidate 與最後一段共線反向延伸,應「取代」末點而非新增(就地化簡)
   existingEdges 是呼叫端傳入的外部邊;自身邊只檢查「排除最後一段(相鄰)」的較早邊段,
   最後一段與新段共享端點,交給 adjacencyRelation 判(與收尾用的是同一個判準)。 */
function evaluateNextPoint(pts, candidate, existingEdges) {
  const last = pts[pts.length - 1];
  if (samePoint(candidate, last)) {
    return { duplicate: true, error: null, extend: false };
  }

  /* 範圍檢查(原則 1 的一部分,GEO-180):點本身根本不在核心支援的座標範圍內時,
     交叉/回頭那些判斷都沒有意義,直接擋。吸附、共線延長、鍵入長度算出來的點
     全都會流經這裡,所以只要擋這一處就夠(首點不經本函式,由 place 另外擋)。 */
  if (!pointInRange(candidate)) {
    return { duplicate: false, error: { code: "OUT_OF_RANGE", msg: OUT_OF_RANGE_MSG }, extend: false };
  }

  let extend = false;
  if (pts.length >= 2) {
    const rel = adjacencyRelation(last, pts[pts.length - 2], candidate);
    if (rel === "overlap") {
      return { duplicate: false, error: { code: "BACKTRACK", msg: "不能沿原邊回頭" }, extend: false };
    }
    if (rel === "collinear-through") extend = true;
  }

  /* 容量檢查(原則 1 的一部分,GEO-179):新點會讓草稿超過核心上限就當場擋下,
     不要讓使用者畫到第 33 點才在送核心時被打回。extend 是取代末點、不增加頂點數,
     所以不受限——擋的是「頂點數」不是「落點動作」。 */
  if (!extend && pts.length >= POLY_MAX_VERTICES) {
    return { duplicate: false, error: { code: "TOO_MANY", msg: TOO_MANY_MSG }, extend };
  }

  const selfEdges = [];
  for (let i = 0; i + 2 < pts.length; ++i) selfEdges.push([pts[i], pts[i + 1]]);
  const allEdges = (existingEdges || []).concat(selfEdges);
  const seg = [last, candidate];
  for (const e of allEdges) {
    if (segmentsIntersect(seg, e)) {
      return { duplicate: false, error: { code: "CROSS", msg: "這段會與既有邊交叉" }, extend };
    }
  }
  return { duplicate: false, error: null, extend };
}

/* ---------------------------------------------------------------- */
/* §3 純函式                                                         */
/* ---------------------------------------------------------------- */

function createState() {
  return { pts: [], cur: null, typed: "", closeReady: false, error: null };
}

function axisLock(pts, freePt) {
  const last = pts[pts.length - 1];
  const dx = freePt[0] - last[0], dy = freePt[1] - last[1];
  if (Math.abs(dx) >= Math.abs(dy)) return [freePt[0], last[1]];
  return [last[0], freePt[1]];
}

function snapToGrid(pt, gridMm) {
  if (!(gridMm > 0)) return pt;
  return [Math.round(pt[0] / gridMm) * gridMm, Math.round(pt[1] / gridMm) * gridMm];
}

function snapToVertices(pt, pts, thresholdScene) {
  let x = pt[0], y = pt[1];
  let bestX = null, bestXDist = Infinity;
  let bestY = null, bestYDist = Infinity;
  for (const p of pts) {
    const dx = Math.abs(p[0] - x);
    if (dx <= thresholdScene && dx < bestXDist) { bestXDist = dx; bestX = p[0]; }
    const dy = Math.abs(p[1] - y);
    if (dy <= thresholdScene && dy < bestYDist) { bestYDist = dy; bestY = p[1]; }
  }
  const guides = [];
  if (bestX !== null) { x = bestX; guides.push({ axis: "x", value: bestX }); }
  if (bestY !== null) { y = bestY; guides.push({ axis: "y", value: bestY }); }
  return { pt: [x, y], guides };
}

/* 落點前置管線:①軸鎖(首點跳過)②格線吸附(若 snapOn)③頂點吸附,回傳 { pt, guides } */
function snapPipeline(pts, freePt, opts) {
  const gridMm = opts.gridMm, snapOn = opts.snapOn;
  const vertexSnapPx = opts.vertexSnapPx === undefined ? 8 : opts.vertexSnapPx;
  const zoom = opts.zoom || 1;
  let pt;
  if (pts.length === 0) {
    pt = [Math.round(freePt[0]), Math.round(freePt[1])];
  } else {
    const locked = axisLock(pts, freePt);
    pt = [Math.round(locked[0]), Math.round(locked[1])];
  }
  if (snapOn) pt = snapToGrid(pt, gridMm);
  const thresholdScene = (vertexSnapPx || 0) / zoom;
  const vs = snapToVertices(pt, pts, thresholdScene);
  return { pt: vs.pt, guides: vs.guides };
}

function place(state, freePt, opts) {
  opts = opts || {};
  const pts = state.pts;
  const { pt: candidate } = snapPipeline(pts, freePt, opts);

  if (pts.length === 0) {
    /* 首點不經 evaluateNextPoint(沒有前一段可比),範圍檢查要在這裡補一次(GEO-180)。 */
    if (!pointInRange(candidate)) {
      return { state, error: { code: "OUT_OF_RANGE", msg: OUT_OF_RANGE_MSG } };
    }
    const newState = Object.assign({}, state,
      { pts: [candidate], cur: null, typed: "", error: null, closeReady: false });
    return { state: newState, error: null };
  }

  const r = evaluateNextPoint(pts, candidate, opts.existingEdges);
  if (r.duplicate) return { state, error: null };
  if (r.error) return { state, error: r.error };

  const newPts = pts.slice();
  if (r.extend) newPts[newPts.length - 1] = candidate;
  else newPts.push(candidate);
  const newState = Object.assign({}, state,
    { pts: newPts, cur: null, typed: "", error: null, closeReady: false });
  return { state: newState, error: null };
}

function previewMove(state, freePt, opts) {
  opts = opts || {};
  const pts = state.pts;
  const zoom = opts.zoom || 1;
  const { pt: cur, guides } = snapPipeline(pts, freePt, opts);

  let error = null;
  if (pts.length >= 1) {
    const r = evaluateNextPoint(pts, cur, opts.existingEdges);
    if (!r.duplicate) error = r.error;
  }

  let closeReady = false;
  if (pts.length >= 3) {
    const start = pts[0];
    const dist = Math.hypot(freePt[0] - start[0], freePt[1] - start[1]);
    closeReady = dist <= 12 / zoom;
  }

  let cornerPreview = null;
  if (closeReady) {
    const cc = computeCornerCandidates(pts);
    if (cc.preferred >= 0) cornerPreview = cc.candidates[cc.preferred];
  }

  return { cur, guides, closeReady, error, cornerPreview };
}

function backspace(state) {
  const pts = state.pts;
  const newPts = pts.length <= 1 ? [] : pts.slice(0, -1);
  return Object.assign({}, state, { pts: newPts, cur: null, typed: "", error: null, closeReady: false });
}

function typeDigit(state, ch) {
  return Object.assign({}, state, { typed: (state.typed || "") + ch });
}

function typeBackspace(state) {
  return Object.assign({}, state, { typed: (state.typed || "").slice(0, -1) });
}

function clearTyped(state) {
  return Object.assign({}, state, { typed: "" });
}

/* 鍵入長度定段。方向由 state.cur 相對末點決定,長度取 state.typed。
   原則 1(GEO-178/G4 根因):產生的新邊與滑鼠落點的新邊走**完全同一道**檢查
   ——舊版直接 concat、不驗任何東西,是繞過 CROSS/BACKTRACK 的唯一管道,G3 就是
   靠它把一個會自交的點塞進草稿。opts.existingEdges 與 place 同義。 */
function applyTypedLength(state, opts) {
  opts = opts || {};
  const noDirection = { code: "NO_DIRECTION", msg: "先移動游標決定方向再輸入長度" };
  if (state.cur === null || state.cur === undefined) {
    return { state, error: noDirection };
  }
  const pts = state.pts;
  if (!pts || pts.length === 0) {
    return { state, error: noDirection };   /* 還沒落第一點,談不上方向(防禦) */
  }
  const last = pts[pts.length - 1];
  const len = Math.round(+state.typed || 0);
  const ux = state.cur[0] - last[0], uy = state.cur[1] - last[1];
  let dx, dy;
  if (Math.abs(ux) >= Math.abs(uy)) { dx = Math.sign(ux) || 1; dy = 0; }
  else { dx = 0; dy = Math.sign(uy) || 1; }
  const newPt = [last[0] + dx * len, last[1] + dy * len];

  const r = evaluateNextPoint(pts, newPt, opts.existingEdges);
  /* len<=0 → 新點與末點重合:比照 place 的重合規則靜默忽略(不落點、不算錯誤), */
  /* 絕不可以像舊版那樣 concat 出一條零長邊。 */
  if (r.duplicate) return { state, error: null };
  if (r.error) return { state, error: r.error };

  const newPts = pts.slice();
  if (r.extend) newPts[newPts.length - 1] = newPt;   /* 與末段共線續走 → 就地延長 */
  else newPts.push(newPt);
  const newState = Object.assign({}, state,
    { pts: newPts, cur: null, typed: "", error: null });
  return { state: newState, error: null };
}

function computeCornerCandidates(pts) {
  const F = pts[0], L = pts[pts.length - 1];
  if (L[0] === F[0] || L[1] === F[1]) return { candidates: [], preferred: -1 };
  const candidates = [[L[0], F[1]], [F[0], L[1]]];
  const prevLast = pts[pts.length - 2];
  const lastSegVertical = prevLast[0] === L[0];
  /* 末段垂直→偏好 L→candidate 為水平的候選(index1);末段水平→偏好 index0 */
  const preferred = lastSegVertical ? 1 : 0;
  return { candidates, preferred };
}

/* 對一個「草稿 + 收尾段」組出的 raw 環下判決(原則 2/3 的執行順序):
     ① 化簡後湊不齊 4 個頂點 → TOO_FEW(形狀還沒成形,比自交更前置)
     ①' 化簡後超過核心上限 → TOO_MANY(容量問題,與形狀無關,同樣前置)
     ② 收尾段(newSegs)碰到 existingEdges → CROSS(外部邊,不在 ring 裡,單獨查)
     ③ raw 環本身不合法(ringGeometryError)→ CROSS
     ④ 化簡後面積為 0 → DEGENERATE(防禦;非自交的正交簡單環面積恆不為 0)
   通過則回 { code: null, pts: 化簡後點列 }。補角分支拿任一 code 當「這個候選不可行」,
   但 TOO_MANY 不會被收斂成 NO_CORNER(見 tryClose)。
   上限比對的是**化簡後**的點列——那才是真正送進核心的東西;拿 raw 去比會把
   「32 點草稿 + 補角 = raw 33 → 化簡回 32」這種完全合法的收尾誤殺。 */
function evaluateClosedRing(ring, newSegs, existingEdges) {
  const simplified = dedupeLoop(ring);
  if (simplified.length < 4) {
    return { code: "TOO_FEW", msg: "外環至少要 4 個非共線頂點" };
  }
  if (simplified.length > POLY_MAX_VERTICES) {
    return { code: "TOO_MANY", msg: TOO_MANY_MSG };
  }
  /* 範圍檢查對**環上每一個頂點**做,對齊 current_geometry.c:239(GEO-180)。補角點的
     兩個座標都抄自既有頂點,自己不可能新超界;真正要擋的是「沒走 place 的呼叫端」
     直接塞進來的超界草稿——attack_coordlimit.js 的 tryClose 就是這樣打穿的。 */
  for (const p of ring) {
    if (!pointInRange(p)) return { code: "OUT_OF_RANGE", msg: OUT_OF_RANGE_MSG };
  }
  for (const seg of newSegs) {
    for (const e of existingEdges) {
      if (segmentsIntersect(seg, e)) return { code: "CROSS", msg: "這段會與既有邊交叉" };
    }
  }
  if (ringGeometryError(ring)) {
    return { code: "CROSS", msg: "這段會與既有邊交叉" };
  }
  if (ringArea2(simplified) === 0) {
    return { code: "DEGENERATE", msg: "這個形狀面積是 0,無法閉合" };
  }
  return { code: null, pts: simplified };
}

function tryClose(state, opts) {
  opts = opts || {};
  const existingEdges = opts.existingEdges || [];
  const pts = (state && state.pts) || [];
  if (pts.length < 3) {
    return { ok: false, error: { code: "TOO_FEW", msg: "外環至少要 4 個非共線頂點" } };
  }
  const F = pts[0], L = pts[pts.length - 1];

  if (L[0] === F[0] || L[1] === F[1]) {
    /* 直接閉合:新增的收尾段是 L→F(環的 wraparound 邊)。整個 raw 環(草稿已定邊
       + 這一段)交給 evaluateClosedRing 總驗證——收尾段的相鄰邊是末段與首段,
       其餘一律不得接觸。 */
    const verdict = evaluateClosedRing(pts.slice(), [[L, F]], existingEdges);
    if (verdict.code) return { ok: false, error: { code: verdict.code, msg: verdict.msg } };
    return { ok: true, pts: verdict.pts };
  }

  /* 補角:兩個候選各自組出完整 raw 環,走同一道總驗證;先試偏好候選(§5.A.1.7 規則 2),
     不可行就退選另一個,兩個都不可行 → NO_CORNER。候選與草稿既有頂點重合(G1)、候選
     讓收尾段壓在草稿自己的邊上(F2)、候選讓化簡把形狀改掉(舊版「退選」案例),都在
     總驗證裡以同一條規則被擋下,不需要個別 gate。 */
  const { candidates, preferred } = computeCornerCandidates(pts);
  const order = preferred === 0 ? [0, 1] : [1, 0];
  let capacity = null;
  for (const idx of order) {
    const cand = candidates[idx];
    const verdict = evaluateClosedRing(pts.concat([cand]), [[L, cand], [cand, F]], existingEdges);
    if (!verdict.code) return { ok: true, pts: verdict.pts };
    /* 容量/座標範圍不是「這個轉折撞到東西」,換另一個轉折也救不了,照實回報,
       不要收斂成 NO_CORNER(那會像 G1 一樣答非所問)。 */
    if ((verdict.code === "TOO_MANY" || verdict.code === "OUT_OF_RANGE") && !capacity) {
      capacity = verdict;
    }
  }
  if (capacity) return { ok: false, error: { code: capacity.code, msg: capacity.msg } };
  return {
    ok: false,
    error: { code: "NO_CORNER", msg: "末段接不回起點——兩個轉折都會撞到既有邊" },
  };
}

/* ---------------------------------------------------------------- */
/* 匯出(UMD 式守衛:瀏覽器掛 window.PolyDraft,Node 走 module.exports) */
/* ---------------------------------------------------------------- */

const PolyDraft = {
  createState,
  axisLock,
  snapToGrid,
  snapToVertices,
  place,
  previewMove,
  backspace,
  typeDigit,
  typeBackspace,
  clearTyped,
  applyTypedLength,
  computeCornerCandidates,
  tryClose,
};

if (typeof module !== "undefined" && module.exports) module.exports = PolyDraft;
else window.PolyDraft = PolyDraft;
