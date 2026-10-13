/*
 * polydraft_test.js — PolyDraft 純函式單元測試 + 跨層裁判
 *
 * 跑法:node geometry-web/polydraft_test.js
 * 只用 node:test + node:assert;不需要 headless Chrome、不需要 bridge、不需要 serve.py。
 *
 * 測試分區(對照 RC-POLYGON-PLAN.md §5.A.1.13 狀態轉移表 / POLYDRAFT-API.md §3-4):
 *   A. snapToGrid            B. axisLock             C. snapToVertices
 *   D. place—格線吸附         E. place—共線延長合併     F. place—BACKTRACK
 *   G. place—CROSS           H. place—首點            I. place—重合忽略
 *   J. previewMove           K. backspace             L. typed 緩衝
 *   M. applyTypedLength      N. computeCornerCandidates
 *   O. tryClose—補直角        P. tryClose—TOO_FEW/DEGENERATE
 *   Q. tryClose—去共線        R. 三種閉合觸發同結果
 *   S. Esc 階梯純狀態部分      T. 狀態轉移表逐邊覆蓋（散於上）
 *   U. tryClose—收尾自交（對抗審查 F1/F2，GEO-176）
 *   V. tryClose—補角候選與既有頂點重合（對抗審查 G1，GEO-177）
 *   W. 對抗審查攻擊腳本逐字回歸（G3/G4，GEO-178）
 *   Y. 頂點上限 POLY_MAX_VERTICES=32（GEO-179；含 core.exe 對 32/33/34 點的實測）
 *   X. 座標範圍 COORD_LIMIT=±1e8（H1，GEO-180；含 core.exe 對 ±1e8 / ±(1e8+1) 的實測）
 *   Z. 跨層裁判（core.exe 交叉確認，§驗收條件 2；含 G2/GEO-177 的錯誤碼對照與
 *      TOO_FEW 不再略過的直接驗證）
 *   Z2/Z3. 跨層裁判續：非單調隨機草稿（GEO-176）、混合 place/applyTypedLength 的
 *      隨機草稿（GEO-178；此前所有隨機產生器都只走 place，鍵入長度這條管道從未被掃過）
 *
 * 全域不變式：assertShapePreserved（見下方「形狀守恆通用斷言」）套在**每一個**
 * tryClose 回 ok 的案例上——手寫案例透過 tryCloseChecked，隨機案例透過
 * judgeAgainstCore。這是擋 G3 那類「去共線偷改形狀」的牙。
 */
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const fs = require("node:fs");
const os = require("node:os");
const { execFileSync } = require("node:child_process");

const PD = require(path.join(__dirname, "polydraft.js"));

/* ---------------------------------------------------------------- */
/* A. snapToGrid                                                    */
/* ---------------------------------------------------------------- */

test("snapToGrid：(113,240) 配 gridMm=250 → 吸附到 (0,250)", () => {
  assert.deepStrictEqual(PD.snapToGrid([113, 240], 250), [0, 250]);
});

test("snapToGrid：(270,240) 配 gridMm=100 → 吸附到 (300,200)", () => {
  assert.deepStrictEqual(PD.snapToGrid([270, 240], 100), [300, 200]);
});

test("snapToGrid：gridMm<=0 → 原樣回傳、不吸附", () => {
  assert.deepStrictEqual(PD.snapToGrid([113, 241], 0), [113, 241]);
  assert.deepStrictEqual(PD.snapToGrid([113, 241], -50), [113, 241]);
});

/* ---------------------------------------------------------------- */
/* B. axisLock                                                      */
/* ---------------------------------------------------------------- */

test("axisLock：|dx|>=|dy| → 鎖 y、x 取自由值", () => {
  assert.deepStrictEqual(PD.axisLock([[0, 0]], [150, 40]), [150, 0]);
});

test("axisLock：|dy|>|dx| → 鎖 x、y 取自由值", () => {
  assert.deepStrictEqual(PD.axisLock([[0, 0]], [40, 150]), [0, 150]);
});

test("axisLock：以 pts 最後一點為基準（非第一點）", () => {
  assert.deepStrictEqual(PD.axisLock([[0, 0], [500, 0]], [520, 300]), [500, 300]);
});

/* ---------------------------------------------------------------- */
/* C. snapToVertices                                                */
/* ---------------------------------------------------------------- */

test("snapToVertices：候選點 x/y 各自落在既有頂點 ±threshold 內 → 兩軸皆吸附、guides 各一筆", () => {
  const pts = [[0, 0], [1000, 0], [1000, 800]];
  const r = PD.snapToVertices([1004, 796], pts, 8);
  assert.deepStrictEqual(r.pt, [1000, 800]);
  assert.strictEqual(r.guides.length, 2);
  assert.ok(r.guides.some(g => g.axis === "x" && g.value === 1000));
  assert.ok(r.guides.some(g => g.axis === "y" && g.value === 800));
});

test("snapToVertices：超出門檻 → 原樣回傳、guides 空陣列", () => {
  const pts = [[0, 0], [1000, 0]];
  const r = PD.snapToVertices([500, 500], pts, 8);
  assert.deepStrictEqual(r.pt, [500, 500]);
  assert.deepStrictEqual(r.guides, []);
});

/* ---------------------------------------------------------------- */
/* D. place — 格線吸附                                               */
/* ---------------------------------------------------------------- */

const baseOpts = (extra) => Object.assign(
  { gridMm: 250, snapOn: true, vertexSnapPx: 8, zoom: 1, existingEdges: [] }, extra);

/* ================================================================ */
/* 形狀守恆通用斷言(GEO-178 的牙,對應 polydraft.js 檔頭原則 2/3)      */
/*                                                                  */
/* tryClose 成功回傳的 pts,必須與「raw 草稿 + 閉合段」是同一個幾何。   */
/* 這條是對抗審查 G3 的直接對策:當時 tryClose 對                      */
/* [[0,0],[0,600],[800,600],[800,300],[0,300]] 回 ok,卻把 F=(0,0) 連同 */
/* 整個突出段一起「化簡」掉,送出一個使用者沒畫的矩形——面積碰巧相等,     */
/* 所以光靠面積斷言抓不到,必須同時查「raw 每個頂點都還在輸出的邊上」。   */
/* 下面四條合起來才等價於「去共線只化簡、不改形狀」:                    */
/*   ① 輸出至少 4 點、每邊軸平行非零長(輸出本身是合法正交環)            */
/*   ② 輸出每個頂點都是 raw 頂點(不得無中生有)                        */
/*   ③ raw 每個頂點都落在輸出多邊形的某條邊上(不得把畫過的地方丟掉)     */
/*   ④ shoelace 有向面積完全相等(含正負號,不得整體翻面/縮水)          */
/* ================================================================ */

function ptEq(a, b) { return a[0] === b[0] && a[1] === b[1]; }

function ringArea2Of(ring) {
  let area2 = 0;
  for (let i = 0; i < ring.length; ++i) {
    const a = ring[i], b = ring[(i + 1) % ring.length];
    area2 += a[0] * b[1] - b[0] * a[1];
  }
  return area2;
}

/* 點是否落在軸平行線段上(含端點) */
function pointOnSegment(p, a, b) {
  if (a[0] === b[0]) {
    return p[0] === a[0] && p[1] >= Math.min(a[1], b[1]) && p[1] <= Math.max(a[1], b[1]);
  }
  if (a[1] === b[1]) {
    return p[1] === a[1] && p[0] >= Math.min(a[0], b[0]) && p[0] <= Math.max(a[0], b[0]);
  }
  return false;
}

function pointOnRing(p, ring) {
  for (let i = 0; i < ring.length; ++i) {
    if (pointOnSegment(p, ring[i], ring[(i + 1) % ring.length])) return true;
  }
  return false;
}

/* 由「草稿 pts」與「tryClose 輸出」還原出 tryClose 內部驗證過的 raw 環:
   輸出裡不屬於草稿的那一個點就是補角頂點(補角點必是真轉角,永遠不會被去共線吃掉;
   而且 GEO-178 後與既有頂點重合的候選一律不可行,所以最多只會有一個)。 */
function rawRingOf(pts, outPts) {
  const extra = outPts.filter(p => !pts.some(q => ptEq(p, q)));
  assert.ok(extra.length <= 1,
    "輸出最多只能比草稿多一個補角頂點,實際多了:" + JSON.stringify(extra));
  if (extra.length === 1) {
    const cc = PD.computeCornerCandidates(pts);
    assert.ok(cc.candidates.some(c => ptEq(c, extra[0])),
      "多出來的頂點必須是 computeCornerCandidates 的候選之一:" + JSON.stringify(extra[0]));
  }
  return pts.concat(extra);
}

function assertShapePreserved(pts, outPts, label) {
  const tag = label ? "[" + label + "] " : "";
  const raw = rawRingOf(pts, outPts);

  /* ① 輸出本身是合法正交環的基本形狀條件 */
  assert.ok(outPts.length >= 4, tag + "輸出至少 4 個頂點:" + JSON.stringify(outPts));
  for (let i = 0; i < outPts.length; ++i) {
    const a = outPts[i], b = outPts[(i + 1) % outPts.length];
    assert.ok(!ptEq(a, b), tag + "輸出不得有零長邊:" + JSON.stringify([a, b]));
    assert.ok(a[0] === b[0] || a[1] === b[1], tag + "輸出每邊必須軸平行:" + JSON.stringify([a, b]));
  }
  /* ② 輸出頂點都來自 raw 環 */
  for (const p of outPts) {
    assert.ok(raw.some(q => ptEq(p, q)),
      tag + "輸出頂點 " + JSON.stringify(p) + " 不在 raw 環裡:" + JSON.stringify(raw));
  }
  /* ③ raw 頂點都還在輸出的邊上(去共線只准拿掉落在邊上的贅點) */
  for (const p of raw) {
    assert.ok(pointOnRing(p, outPts),
      tag + "raw 頂點 " + JSON.stringify(p) + " 不在輸出多邊形的邊上——形狀被改掉了。" +
      "raw=" + JSON.stringify(raw) + " out=" + JSON.stringify(outPts));
  }
  /* ④ 有向面積完全相等 */
  assert.strictEqual(ringArea2Of(outPts), ringArea2Of(raw),
    tag + "去共線前後 shoelace 有向面積必須相等:raw=" + JSON.stringify(raw) +
    " out=" + JSON.stringify(outPts));
  assert.notStrictEqual(ringArea2Of(outPts), 0, tag + "輸出面積不得為 0");
}

/* tryClose + 形狀守恆斷言的包裝:所有會走到 tryClose 的測試一律用這個,
   確保新舊案例(含兩組隨機產生器)都被同一條不變式管住。 */
function tryCloseChecked(st, opts, label) {
  const r = PD.tryClose(st, opts || { existingEdges: [] });
  if (r.ok) assertShapePreserved(st.pts, r.pts, label);
  return r;
}

test("place：snapOn=true、gridMm=250 → 新頂點座標是 250 的整數倍", () => {
  let s = PD.createState();
  s = PD.place(s, [10, 10], baseOpts()).state;           // 起點
  const r = PD.place(s, [640, 30], baseOpts());
  assert.strictEqual(r.error, null);
  const p = r.state.pts[r.state.pts.length - 1];
  assert.strictEqual(p[0] % 250, 0);
});

test("place：snapOn=false → 不吸附格線，頂點可為非 250 倍數", () => {
  let s = PD.createState();
  s = PD.place(s, [10, 10], baseOpts({ snapOn: false })).state;
  const r = PD.place(s, [643, 12], baseOpts({ snapOn: false }));
  const p = r.state.pts[r.state.pts.length - 1];
  assert.strictEqual(p[0], 643);
});

/* ---------------------------------------------------------------- */
/* E. place — 共線延長合併                                           */
/* ---------------------------------------------------------------- */

test("place：沿最後一段同軸同向落點 → 取代末頂點（延長合併，不新增）", () => {
  let s = PD.createState();
  s = PD.place(s, [0, 0], baseOpts({ snapOn: false })).state;
  s = PD.place(s, [500, 0], baseOpts({ snapOn: false })).state;   // 第一段 +x 500
  assert.strictEqual(s.pts.length, 2);
  const r = PD.place(s, [900, 3], baseOpts({ snapOn: false }));   // 同軸延長到 900
  assert.strictEqual(r.error, null);
  assert.strictEqual(r.state.pts.length, 2);                       // 沒有新增頂點
  assert.deepStrictEqual(r.state.pts[1], [900, 0]);
});

/* ---------------------------------------------------------------- */
/* F. place — BACKTRACK                                             */
/* ---------------------------------------------------------------- */

test("place：沿最後一段同軸反向落點 → BACKTRACK 拒絕、state 不變", () => {
  let s = PD.createState();
  s = PD.place(s, [0, 0], baseOpts({ snapOn: false })).state;
  s = PD.place(s, [500, 0], baseOpts({ snapOn: false })).state;   // 最後一段方向 +x
  const r = PD.place(s, [100, 2], baseOpts({ snapOn: false }));    // 同軸但反向（-x）
  assert.strictEqual(r.error && r.error.code, "BACKTRACK");
  assert.strictEqual(r.state, s);
});

/* ---------------------------------------------------------------- */
/* G. place — CROSS                                                 */
/* ---------------------------------------------------------------- */

test("place：新段與較早的既有邊（非相鄰）相交 → CROSS 拒絕、state 不變", () => {
  let s = PD.createState();
  const o = baseOpts({ snapOn: false });
  s = PD.place(s, [0, 0], o).state;
  s = PD.place(s, [1000, 0], o).state;     // edge0：(0,0)-(1000,0)
  s = PD.place(s, [1000, 1000], o).state;  // edge1：(1000,0)-(1000,1000)
  s = PD.place(s, [400, 1000], o).state;   // edge2：(1000,1000)-(400,1000)
  const r = PD.place(s, [400, -500], o);   // 下探，穿過 edge0
  assert.strictEqual(r.error && r.error.code, "CROSS");
  assert.strictEqual(r.state, s);
});

test("place：existingEdges（呼叫端給的外部邊）也納入 CROSS 檢查", () => {
  let s = PD.createState();
  const ext = [[[0, -100], [0, 500]]];  // 一條外部垂直邊 x=0
  const o = baseOpts({ snapOn: false, existingEdges: ext });
  s = PD.place(s, [200, 0], o).state;
  const r = PD.place(s, [-300, 3], o);  // 水平段跨過 x=0 的外部邊
  assert.strictEqual(r.error && r.error.code, "CROSS");
});

/* ---------------------------------------------------------------- */
/* H. place — 首點                                                  */
/* ---------------------------------------------------------------- */

test("place：pts 為空，落第一點 → pts 變成單一頂點、不軸鎖", () => {
  const s = PD.createState();
  const r = PD.place(s, [123, 456], baseOpts({ snapOn: false }));
  assert.strictEqual(r.error, null);
  assert.deepStrictEqual(r.state.pts, [[123, 456]]);
});

/* ---------------------------------------------------------------- */
/* I. place — 候選點與末點重合忽略                                    */
/* ---------------------------------------------------------------- */

test("place：候選點與末點重合 → state 不變、error null（忽略,不算 BACKTRACK）", () => {
  let s = PD.createState();
  s = PD.place(s, [0, 0], baseOpts({ snapOn: false })).state;
  const r = PD.place(s, [0, 0], baseOpts({ snapOn: false }));
  assert.strictEqual(r.error, null);
  assert.strictEqual(r.state, s);
});

/* ---------------------------------------------------------------- */
/* J. previewMove                                                   */
/* ---------------------------------------------------------------- */

test("previewMove：pts>=3 且 cur 落在 12px/zoom 閉合半徑內 → closeReady=true", () => {
  let s = PD.createState();
  const o = baseOpts({ snapOn: false, zoom: 1 });
  s = PD.place(s, [0, 0], o).state;
  s = PD.place(s, [1000, 0], o).state;
  s = PD.place(s, [1000, 1000], o).state;
  const pm = PD.previewMove(s, [3, -4], o);   // 距起點 (0,0) 5 scene mm，遠小於 12
  assert.strictEqual(pm.closeReady, true);
});

test("previewMove：距起點超出 12px/zoom → closeReady=false", () => {
  let s = PD.createState();
  const o = baseOpts({ snapOn: false, zoom: 1 });
  s = PD.place(s, [0, 0], o).state;
  s = PD.place(s, [1000, 0], o).state;
  s = PD.place(s, [1000, 1000], o).state;
  const pm = PD.previewMove(s, [100, 100], o);
  assert.strictEqual(pm.closeReady, false);
});

test("previewMove（GEO-185 #2）：閉合就緒且可以閉合 → error 為 null，不得把收尾段當普通下一點報 CROSS", () => {
  let s = PD.createState();
  const o = baseOpts({ snapOn: true, gridMm: 250, zoom: 1 });
  for (const p of [[0, 0], [250, 0], [250, 250], [0, 250]]) s = PD.place(s, p, o).state;
  const pm = PD.previewMove(s, [2, 2], o);   // 吸附後 cur 正好落在起點——舊版在這裡報 CROSS
  assert.strictEqual(pm.closeReady, true);
  assert.strictEqual(PD.tryClose(s, { existingEdges: [] }).ok, true);
  assert.strictEqual(pm.error, null);
});

test("previewMove（GEO-185 #2）：閉合就緒但閉合不可行 → error 與 tryClose 同碼", () => {
  const blockBoth = [[[300, 100], [300, 300]], [[400, -100], [400, 100]]];
  const s = { pts: CORNER_DRAFT, cur: null, typed: "", closeReady: false, error: null };
  const o = baseOpts({ snapOn: false, zoom: 1, existingEdges: blockBoth });
  const pm = PD.previewMove(s, [CORNER_DRAFT[0][0] + 3, CORNER_DRAFT[0][1] + 3], o);
  assert.strictEqual(pm.closeReady, true);
  assert.strictEqual(pm.error && pm.error.code, PD.tryClose(s, { existingEdges: blockBoth }).error.code);
});

test("previewMove：zoom 影響閉合半徑（scene 距離 = 12/zoom）", () => {
  let s = PD.createState();
  const o = baseOpts({ snapOn: false, zoom: 1 });
  s = PD.place(s, [0, 0], o).state;
  s = PD.place(s, [1000, 0], o).state;
  s = PD.place(s, [1000, 1000], o).state;
  const pm = PD.previewMove(s, [20, 0], baseOpts({ snapOn: false, zoom: 2 })); // 20 scene mm，門檻 12/2=6
  assert.strictEqual(pm.closeReady, false);
});

test("previewMove：末點與起點不同軸且 closeReady → cornerPreview 回傳偏好候選", () => {
  let s = PD.createState();
  const o = baseOpts({ snapOn: false });
  s = PD.place(s, [0, 0], o).state;
  s = PD.place(s, [1000, 0], o).state;
  s = PD.place(s, [1000, 800], o).state;   // 末點(1000,800) 與起點(0,0) 不同軸
  const pm = PD.previewMove(s, [2, -1], o);
  assert.ok(pm.closeReady);
  assert.ok(Array.isArray(pm.cornerPreview));
  const { candidates, preferred } = PD.computeCornerCandidates(s.pts);
  assert.deepStrictEqual(pm.cornerPreview, candidates[preferred]);
});

test("previewMove：末點與起點同軸 → cornerPreview 為 null", () => {
  let s = PD.createState();
  const o = baseOpts({ snapOn: false });
  s = PD.place(s, [0, 0], o).state;
  s = PD.place(s, [1000, 0], o).state;
  s = PD.place(s, [1000, 800], o).state;
  s = PD.place(s, [0, 800], o).state;      // 末點(0,800) 與起點(0,0) 同 x 軸
  const pm = PD.previewMove(s, [2, -1], o);
  assert.strictEqual(pm.cornerPreview, null);
});

test("previewMove：CROSS 情境下回傳 error.code=CROSS（不落點、只預覽）", () => {
  let s = PD.createState();
  const o = baseOpts({ snapOn: false });
  s = PD.place(s, [0, 0], o).state;
  s = PD.place(s, [1000, 0], o).state;
  s = PD.place(s, [1000, 1000], o).state;
  s = PD.place(s, [400, 1000], o).state;
  const pm = PD.previewMove(s, [400, -500], o);
  assert.strictEqual(pm.error && pm.error.code, "CROSS");
  assert.strictEqual(s.pts.length, 4);       // previewMove 真的沒有落點
});

test("previewMove：先前游標在會 CROSS 的位置，移到安全位置後 error 恢復 null（狀態轉移表『移開游標→回2/3/4』）", () => {
  let s = PD.createState();
  const o = baseOpts({ snapOn: false });
  s = PD.place(s, [0, 0], o).state;
  s = PD.place(s, [1000, 0], o).state;
  s = PD.place(s, [1000, 1000], o).state;
  s = PD.place(s, [400, 1000], o).state;
  const bad = PD.previewMove(s, [400, -500], o);
  assert.strictEqual(bad.error && bad.error.code, "CROSS");
  const safe = PD.previewMove(s, [400, 1400], o);
  assert.strictEqual(safe.error, null);
});

/* ---------------------------------------------------------------- */
/* K. backspace                                                     */
/* ---------------------------------------------------------------- */

test("backspace：pts>=2 → 移除最後一個頂點", () => {
  const s = { pts: [[0, 0], [500, 0], [500, 300]], cur: [1, 1], typed: "12", closeReady: false, error: null };
  const r = PD.backspace(s);
  assert.deepStrictEqual(r.pts, [[0, 0], [500, 0]]);
  assert.strictEqual(r.cur, null);
  assert.strictEqual(r.typed, "");
  assert.strictEqual(r.error, null);
});

test("backspace：pts 只剩 1 個 → 清空整個 pts（回到『未落筆』狀態，狀態轉移表 2→1）", () => {
  const s = { pts: [[0, 0]], cur: null, typed: "", closeReady: false, error: null };
  const r = PD.backspace(s);
  assert.deepStrictEqual(r.pts, []);
});

/* ---------------------------------------------------------------- */
/* L. typed 緩衝                                                    */
/* ---------------------------------------------------------------- */

test("typeDigit：連續輸入數字 → typed 累積字串（狀態轉移表 2→3）", () => {
  let s = PD.createState();
  s = PD.typeDigit(s, "1");
  s = PD.typeDigit(s, "5");
  s = PD.typeDigit(s, "0");
  s = PD.typeDigit(s, "0");
  assert.strictEqual(s.typed, "1500");
});

test("typeBackspace：去掉 typed 最後一字元", () => {
  let s = PD.createState();
  s = PD.typeDigit(s, "1");
  s = PD.typeDigit(s, "2");
  s = PD.typeBackspace(s);
  assert.strictEqual(s.typed, "1");
});

test("clearTyped：typed 清空、pts 不受影響（Esc 第一層）", () => {
  let s = PD.createState();
  s.pts = [[0, 0], [500, 0]];
  s = PD.typeDigit(s, "9");
  const r = PD.clearTyped(s);
  assert.strictEqual(r.typed, "");
  assert.deepStrictEqual(r.pts, [[0, 0], [500, 0]]);
});

/* ---------------------------------------------------------------- */
/* M. applyTypedLength                                              */
/* ---------------------------------------------------------------- */

test("applyTypedLength：state.cur 為 null → NO_DIRECTION、state 不變", () => {
  const s = PD.createState();
  s.pts = [[0, 0]];
  const r = PD.applyTypedLength(s, {});
  assert.strictEqual(r.error && r.error.code, "NO_DIRECTION");
  assert.strictEqual(r.state, s);
});

test("applyTypedLength：cur 在 +x 方向、typed='1500' → 新點距末點 1500、方向 +x", () => {
  let s = PD.createState();
  s.pts = [[0, 0]];
  s.cur = [900, 10];       // |dx|>=|dy| → +x 方向
  s.typed = "1500";
  const r = PD.applyTypedLength(s, {});
  assert.strictEqual(r.error, null);
  assert.deepStrictEqual(r.state.pts, [[0, 0], [1500, 0]]);
  assert.strictEqual(r.state.typed, "");
  assert.strictEqual(r.state.cur, null);
});

test("applyTypedLength：新段與草稿較早的邊相交 → CROSS、state 不變（GEO-178/G4 根因：" +
  "舊版完全不驗,是唯一能繞過 place() 檢查把自交點塞進草稿的管道）", () => {
  /* 逐字取自對抗審查 G3 的攻擊腳本 attack_g3.js(scratchpad/clarify/):
     place 依序落 [0,0] [0,600] [800,600] [800,300](純 place 序列走不到違規),
     再用 applyTypedLength 往 -x 走 800 直接跳到 (0,300)——它正落在首段
     (0,0)-(0,600) 的中段。修前 error 為 null 且真的落點,修後必須回 CROSS。 */
  const o = baseOpts({ snapOn: false, existingEdges: [] });
  let s = PD.createState();
  for (const p of [[0, 0], [0, 600], [800, 600], [800, 300]]) {
    const r = PD.place(s, p, o);
    assert.strictEqual(r.error, null, "攻擊腳本的落點本身不應被 place() 擋下");
    s = r.state;
  }
  const typedState = Object.assign({}, s, { cur: [-100, 300], typed: "800" });
  const r2 = PD.applyTypedLength(typedState, { existingEdges: [] });
  assert.strictEqual(r2.error && r2.error.code, "CROSS",
    "鍵入長度產生的新段必須與滑鼠落點走同一道檢查；實際：" + JSON.stringify(r2.error));
  assert.strictEqual(r2.state, typedState, "CROSS 時不得落點（state 原樣回傳）");
});

test("applyTypedLength：新段沿最後一段同軸反向 → BACKTRACK、state 不變", () => {
  const st = { pts: [[0, 0], [1000, 0]], cur: [900, 0], typed: "400", closeReady: false, error: null };
  const r = PD.applyTypedLength(st, { existingEdges: [] });
  assert.strictEqual(r.error && r.error.code, "BACKTRACK");
  assert.strictEqual(r.state, st);
});

test("applyTypedLength：新段與 existingEdges 相交 → CROSS、state 不變", () => {
  const st = { pts: [[0, 0], [1000, 0]], cur: [1000, 100], typed: "500", closeReady: false, error: null };
  const ext = [[[800, 200], [1200, 200]]];   // 水平邊 y=200,擋住 (1000,0)→(1000,500)
  const r = PD.applyTypedLength(st, { existingEdges: ext });
  assert.strictEqual(r.error && r.error.code, "CROSS");
  assert.strictEqual(r.state, st);
});

test("applyTypedLength：新段沿最後一段同軸同向 → 延長合併（取代末頂點,不新增）", () => {
  const st = { pts: [[0, 0], [1000, 0]], cur: [1100, 0], typed: "500", closeReady: false, error: null };
  const r = PD.applyTypedLength(st, {});
  assert.strictEqual(r.error, null);
  assert.deepStrictEqual(r.state.pts, [[0, 0], [1500, 0]],
    "共線續走要就地延長（與 place 的共線延長合併同一條規則）,不得留下三點共線的草稿");
});

test("applyTypedLength：typed 長度為 0（新點與末點重合）→ 靜默忽略、不得產生零長邊", () => {
  const st = { pts: [[0, 0], [1000, 0]], cur: [1100, 0], typed: "0", closeReady: false, error: null };
  const r = PD.applyTypedLength(st, {});
  assert.strictEqual(r.error, null);
  assert.strictEqual(r.state, st, "比照 place 的重合規則：state 原樣回傳");
});

test("applyTypedLength：cur 在 -y 方向、typed='800' → 新點方向 -y", () => {
  let s = PD.createState();
  s.pts = [[0, 500]];
  s.cur = [3, 100];        // dy=-400，|dy|>|dx| → -y 方向
  s.typed = "800";
  const r = PD.applyTypedLength(s, {});
  assert.deepStrictEqual(r.state.pts, [[0, 500], [0, -300]]);
});

/* ---------------------------------------------------------------- */
/* N. computeCornerCandidates                                       */
/* ---------------------------------------------------------------- */

test("computeCornerCandidates：末點與起點不同軸 → 回傳兩候選，preferred 指向與末段交錯者", () => {
  const pts = [[0, 0], [1000, 0], [1000, 800]];  // 末段(1000,0)->(1000,800) 垂直
  const r = PD.computeCornerCandidates(pts);
  assert.strictEqual(r.candidates.length, 2);
  assert.deepStrictEqual(r.candidates[0], [1000, 0]);   // [L.x,F.y]
  assert.deepStrictEqual(r.candidates[1], [0, 800]);    // [F.x,L.y]
  // 末段是垂直邊 → 偏好與其交錯（水平）的候選，即 L->candidate 為水平邊的那個 = index1
  assert.strictEqual(r.preferred, 1);
});

test("computeCornerCandidates：末點與起點同軸 → candidates 空、preferred=-1", () => {
  const pts = [[0, 0], [1000, 0], [1000, 800], [0, 800]];
  const r = PD.computeCornerCandidates(pts);
  assert.deepStrictEqual(r.candidates, []);
  assert.strictEqual(r.preferred, -1);
});

/* ---------------------------------------------------------------- */
/* O. tryClose — 補直角                                              */
/* ---------------------------------------------------------------- */

test("tryClose：唯一（偏好）候選合法 → 直接使用該候選閉合", () => {
  const state = { pts: [[0, 0], [1000, 0], [1000, 800]], cur: null, typed: "", closeReady: true, error: null };
  const r = tryCloseChecked(state, { existingEdges: [] }, "唯一候選");
  assert.strictEqual(r.ok, true);
  assert.strictEqual(r.pts.length, 4);
  assert.ok(r.pts.some(p => p[0] === 0 && p[1] === 800));
});

/* 「退選」與「兩候選皆不可行」共用的乾淨草稿(GEO-178 重挑):
     (0,0)→(0,-400)→(1500,-400)→(1500,800)→(700,800)→(700,200)
   末段 (700,800)-(700,200) 垂直 → 偏好候選 = index1 = [F.x,L.y] = (0,200);
   退選候選 = index0 = [L.x,F.y] = (700,0)。
   這個形狀難得地讓**兩個候選各自都能組出合法的簡單環**(不靠去共線救場):
     - 候選 (0,200):收尾段 (0,200)→(0,0) 與首段 (0,0)→(0,-400) 共線但朝相反側,
       只共享 F 這一點 → 合法,F 是共線贅點,化簡掉不改形狀。
     - 候選 (700,0):L→cand 與末段共線但朝相反側,只共享 L 這一點 → 合法,L 是贅點。
   所以用 existingEdges 擋掉其中一個時,退選出來的另一個是真的可行,才測得到「退選」
   而不是「靠化簡把突出段丟掉硬湊出 ok」(那是舊測試的病,見下面的 GEO-178 回歸)。 */
const CORNER_DRAFT = [[0, 0], [0, -400], [1500, -400], [1500, 800], [700, 800], [700, 200]];

test("tryClose：偏好候選與既有邊交叉 → 退而選另一候選", () => {
  const o = baseOpts({ snapOn: false, existingEdges: [] });
  let s = PD.createState();
  for (const p of CORNER_DRAFT) {
    const r = PD.place(s, p, o);
    assert.strictEqual(r.error, null, "草稿本身要能被 place() 逐點畫出來：" + JSON.stringify(p));
    s = r.state;
  }
  const cc = PD.computeCornerCandidates(s.pts);
  assert.deepStrictEqual(cc.candidates[cc.preferred], [0, 200], "測試前提：偏好候選是 (0,200)");
  // 擋住偏好候選 (0,200) 的收尾段 (700,200)-(0,200):一條垂直邊穿過 y=200;
  // 它不會碰到退選候選 (700,0) 的兩段新邊(x=700 那段與它不同 x;y=0 那段不在 y∈[100,300])。
  const blockPreferred = [[[300, 100], [300, 300]]];
  const r = tryCloseChecked(s, { existingEdges: blockPreferred }, "退選");
  assert.strictEqual(r.ok, true);
  assert.ok(r.pts.some(p => p[0] === 700 && p[1] === 0), "應退選到候選 (700,0)");
  assert.ok(!r.pts.some(p => p[0] === 0 && p[1] === 200), "被擋下的偏好候選不應出現在結果中");
});

test("tryClose：兩個候選都與既有邊交叉 → NO_CORNER、不閉合", () => {
  const blockBoth = [
    [[300, 100], [300, 300]],    // 擋住偏好候選 (0,200) 的收尾段 (700,200)-(0,200)
    [[400, -100], [400, 100]],   // 擋住退選候選 (700,0) 的收尾段 (700,0)-(0,0)
  ];
  const r = PD.tryClose(
    { pts: CORNER_DRAFT, cur: null, typed: "", closeReady: true, error: null },
    { existingEdges: blockBoth });
  assert.strictEqual(r.ok, false);
  assert.strictEqual(r.error.code, "NO_CORNER");
});

test("tryClose（GEO-178 回歸）：兩個補角候選都會讓收尾段壓在草稿自己的邊上 → NO_CORNER，" +
  "不得靠去共線把突出段丟掉硬湊出 ok", () => {
  // 這正是 GEO-177 版「退選」測試用的草稿,當時它回 ok:true —— 但那個 ok 是假的:
  //   草稿 (0,0)→(1000,0)→(1000,500)→(1600,500),候選 (0,500) 的收尾段
  //   (1600,500)→(0,500) 整段壓在末段 (1000,500)-(1600,500) 上;去共線把 (1600,500)
  //   吃掉之後剛好剩一個漂亮的矩形 (0,0)(1000,0)(1000,500)(0,500)——core.exe 對那個
  //   矩形 ACCEPT、對 raw 5 點環 REJECT,跟 G3 完全同一種病:使用者畫到 x=1600 的那段
  //   被靜默丟掉,送出的不是他畫的形狀。另一個候選 (1600,0) 同理壓在首段上。
  //   新原則(polydraft.js 檔頭原則 2)在 raw 幾何上判,兩個候選都不可行 → NO_CORNER。
  const pts = [[0, 0], [1000, 0], [1000, 500], [1600, 500]];
  const r = PD.tryClose({ pts, cur: null, typed: "", closeReady: true, error: null },
    { existingEdges: [] });
  assert.strictEqual(r.ok, false, "收尾段壓在草稿自己的邊上,不能算閉合成功");
  assert.strictEqual(r.error.code, "NO_CORNER");
});

/* ---------------------------------------------------------------- */
/* P. tryClose — TOO_FEW / DEGENERATE                                */
/* ---------------------------------------------------------------- */

test("tryClose：去共線後頂點數 <4 → TOO_FEW", () => {
  // 三點共線、且 L/F 已同軸(不需補角):(0,0)-(500,0)-(1000,0) 全部 y=0。
  // 去共線是以「原陣列鄰居」單一 pass 判斷(等同既有 feDedupe),三點互為鄰居又都共線,
  // 三點會全部被判定為共線而移除,剩 0 點,遠低於 4 → TOO_FEW。
  const pts = [[0, 0], [500, 0], [1000, 0]];
  const r = PD.tryClose({ pts, cur: null, typed: "", closeReady: true, error: null },
    { existingEdges: [] });
  assert.strictEqual(r.ok, false);
  assert.strictEqual(r.error.code, "TOO_FEW");
});

test("tryClose：bowtie（自交且淨面積為 0）→ GEO-176 修復後在自交檢查就被擋下，回 CROSS 而非 DEGENERATE", () => {
  // 這個 bowtie 形狀(0,0)→(4000,0)→(4000,2000)→(2000,2000)→(2000,-2000)→(0,-2000)
  // →close(0,0)本身是自交的:邊(0,0)-(4000,0)與邊(2000,2000)-(2000,-2000)相交,
  // 且末段(0,-2000)與起點(0,0)同 x 軸(免補角)——GEO-176 修復前,tryClose 對「直接
  // 閉合」完全不跑交叉檢查,這個自交只靠 shoelace 面積剛好等於 0 的巧合被攔下,
  // 錯把「自交」誤判成「退化」;GEO-176 修復後,收尾段(直接閉合這段,即 pts 末點
  // 接回首點的 wraparound 邊)會一起進 raw 環的總驗證(GEO-178 起是 ringGeometryError),
  // 在到達 shoelace 檢查前就以 CROSS 擋下——這與 current_geometry.c::poly_loop_is_valid
  // 的判斷順序一致(該函式也是先查非相鄰邊相交,自交就直接 return false,永遠不會走到
  // 面積檢查)。
  // DEGENERATE(shoelace 面積為 0 但通過自交檢查)的程式碼路徑依驗收條件保留,但對
  // 正交多邊形而言,一個「非自交」的簡單環面積恆不為 0,所以這條路徑目前找不到能
  // 觸發它、又不會先被自交檢查擋下的合法建構——保留為防禦性程式碼(對齊
  // poly_loop_is_valid 的兩段式檢查結構),不強造一個不自然的案例。
  const pts = [[0, 0], [4000, 0], [4000, 2000], [2000, 2000], [2000, -2000], [0, -2000]];
  const r = PD.tryClose({ pts, cur: null, typed: "", closeReady: true, error: null },
    { existingEdges: [] });
  assert.strictEqual(r.ok, false);
  assert.strictEqual(r.error.code, "CROSS");
});

/* ---------------------------------------------------------------- */
/* Q. tryClose — 去共線                                              */
/* ---------------------------------------------------------------- */

test("tryClose：共線頂點於閉合前被移除", () => {
  const pts = [[0, 0], [500, 0], [1000, 0], [1000, 800]];  // (500,0) 與相鄰兩點共線
  const r = tryCloseChecked({ pts, cur: null, typed: "", closeReady: true, error: null },
    { existingEdges: [] }, "去共線");
  assert.strictEqual(r.ok, true);
  assert.ok(!r.pts.some(p => p[0] === 500 && p[1] === 0));
  // 形狀守恆(assertShapePreserved 已驗):被拿掉的 (500,0) 仍落在輸出的邊上,面積不變。
});

/* ---------------------------------------------------------------- */
/* Q2. tryClose — dropped（GEO-193，補角把剛畫的轉折併掉要提示）        */
/* ---------------------------------------------------------------- */

test("tryClose（GEO-193）：缺口案例——補角把使用者畫的轉折併成直線 → dropped=[[3000,1000]]", () => {
  // 草稿 (0,0)(4000,0)(4000,1000)(3000,1000)，Enter 補 (0,1000) 閉合成 4000×1000 矩形，
  // (3000,1000) 與相鄰兩點共線被去共線吃掉——這正是「缺口靜默消失」的案例，只提示不擋。
  const pts = [[0, 0], [4000, 0], [4000, 1000], [3000, 1000]];
  const r = tryCloseChecked({ pts, cur: null, typed: "", closeReady: true, error: null },
    { existingEdges: [] }, "GEO-193 缺口");
  assert.strictEqual(r.ok, true);
  assert.deepStrictEqual(r.pts.slice().sort(), [[0, 0], [0, 1000], [4000, 0], [4000, 1000]].sort());
  assert.deepStrictEqual(r.dropped, [[3000, 1000]]);
});

test("tryClose（GEO-193）：少畫最後一段案例——同樣併角，即使結果是使用者想要的矩形也照樣回報 dropped", () => {
  // 草稿 (0,0)(4000,0)(4000,3000)(2000,3000)，Enter 補 (0,3000) 閉合成 4000×3000 矩形；
  // 這是使用者故意少畫最後一段、想要的結果，但幾何上無法與「缺口案例」區分，
  // 所以 dropped 照樣回報(3000,1000)... 這裡是 (2000,3000)，由呼叫端決定要不要提示。
  const pts = [[0, 0], [4000, 0], [4000, 3000], [2000, 3000]];
  const r = tryCloseChecked({ pts, cur: null, typed: "", closeReady: true, error: null },
    { existingEdges: [] }, "GEO-193 少畫一段");
  assert.strictEqual(r.ok, true);
  assert.deepStrictEqual(r.pts.slice().sort(), [[0, 0], [0, 3000], [4000, 0], [4000, 3000]].sort());
  assert.deepStrictEqual(r.dropped, [[2000, 3000]]);
});

test("tryClose（GEO-193）：直接同軸閉合（不補角）→ dropped=[]", () => {
  const pts = [[0, 0], [1000, 0], [1000, 800], [0, 800]];
  const r = tryCloseChecked({ pts, cur: null, typed: "", closeReady: true, error: null },
    { existingEdges: [] }, "GEO-193 直接閉合");
  assert.strictEqual(r.ok, true);
  assert.deepStrictEqual(r.dropped, []);
});

/* ---------------------------------------------------------------- */
/* R. 三種閉合觸發（點回起點 12px / Enter / 雙擊）得到同一結果          */
/* ---------------------------------------------------------------- */

test("tryClose：三種觸發方式（點回起點/Enter/雙擊）在相同 state 下呼叫結果一致", () => {
  const build = () => {
    let s = PD.createState();
    const o = baseOpts({ snapOn: false });
    s = PD.place(s, [0, 0], o).state;
    s = PD.place(s, [1000, 0], o).state;
    s = PD.place(s, [1000, 800], o).state;
    s = PD.place(s, [0, 800], o).state;
    return s;
  };
  const viaClickNearStart = build();   // 呼叫端偵測到點擊落在 12px 半徑內 → 呼叫 tryClose
  const viaEnterKey = build();          // 呼叫端偵測到 Enter → 呼叫 tryClose
  const viaDblClick = build();          // 呼叫端偵測到雙擊 → 呼叫 tryClose
  const r1 = tryCloseChecked(viaClickNearStart, { existingEdges: [] }, "三種觸發");
  const r2 = PD.tryClose(viaEnterKey, { existingEdges: [] });
  const r3 = PD.tryClose(viaDblClick, { existingEdges: [] });
  assert.deepStrictEqual(r1, r2);
  assert.deepStrictEqual(r2, r3);
});

/* ---------------------------------------------------------------- */
/* U. tryClose — 收尾自交（對抗審查 F1/F2，GEO-176）                    */
/*    F1/F2 逐字取自對抗審查員的攻擊腳本(attack1.js/attack2.js，        */
/*    scratchpad/clarify/)；修前皆紅(tryClose 誤回 ok:true，core.exe    */
/*    以「不自交」規則拒絕同一 outline)，修後皆綠。                      */
/* ---------------------------------------------------------------- */

test("tryClose：F1——末點與起點已同軸（免補角）時直接閉合，跳過交叉檢查 → 攻擊前 ok:true 但收尾段自交，修後須擋下", () => {
  const o = baseOpts({ snapOn: false, existingEdges: [] });
  let s = PD.createState();
  const pts = [[0, 0], [0, 500], [200, 500], [200, -500], [600, -500], [600, 0]];
  for (const p of pts) {
    const r = PD.place(s, p, o);
    assert.strictEqual(r.error, null, "攻擊腳本的落點本身不應被 place() 擋下：" + JSON.stringify(p));
    s = r.state;
  }
  // 末點 (600,0) 與起點 (0,0) 同 y 軸，直接閉合；但直接閉合段 (600,0)-(0,0) 會與
  // 較早的邊 (200,500)-(200,-500) 交叉（core.exe 對同一 outline 判「不自交」失敗，
  // exit 1）。tryClose 必須把這段收尾也當成「新增段」跑交叉檢查，回 CROSS 而非 ok:true。
  const r = PD.tryClose(s, { existingEdges: [] });
  assert.strictEqual(r.ok, false, "F1：收尾段自交，tryClose 不應回 ok:true");
  assert.strictEqual(r.error && r.error.code, "CROSS");
});

test("tryClose：F2——補直角候選只用 existingEdges 擋交叉、不比對草稿自身邊 → 攻擊前選中會自交的偏好候選，修後兩候選皆須被擋、回 NO_CORNER", () => {
  // 主畫布 P 的 existingEdges 依 POLYDRAFT-API.md §5 永遠是 []（新面沒有既有邊），
  // 補角候選的可行性過去只對這個空陣列做 .some(...)，等於完全不驗。
  const o = baseOpts({ snapOn: false, existingEdges: [] });
  let s = PD.createState();
  const pts = [[0, 0], [0, 800], [500, 800], [500, -2000], [3000, -2000], [3000, 600]];
  for (const p of pts) {
    const r = PD.place(s, p, o);
    assert.strictEqual(r.error, null, "攻擊腳本的落點本身不應被 place() 擋下：" + JSON.stringify(p));
    s = r.state;
  }
  // 末點 (3000,600) 與起點 (0,0) 不同軸，需要補角。偏好候選 (0,600)（L→cand 水平，
  // 因末段垂直而偏好）會與草稿自身的邊 (500,800)-(500,-2000) 交叉；退選候選
  // (3000,0)（L→cand 垂直）與末段共線回頭、且會與收尾邊 (cand,F) 撞上草稿自身邊。
  // 兩個候選在正確的「含自身邊」檢查下都不合法 → NO_CORNER；攻擊前的舊版只查
  // existingEdges=[]，永遠判定偏好候選可行，直接誤選出會自交的多邊形。
  const r = PD.tryClose(s, { existingEdges: [] });
  assert.strictEqual(r.ok, false, "F2：兩個補角候選都會撞到草稿自身邊，tryClose 不應回 ok:true");
  assert.strictEqual(r.error && r.error.code, "NO_CORNER");
});

/* ---------------------------------------------------------------- */
/* V. tryClose — 補角候選與既有頂點重合（對抗審查 G1，GEO-177）        */
/*    G1 逐字取自對抗審查員的攻擊腳本(attack_dup.js/dup_raw.scene，     */
/*    scratchpad/clarify/)；修前紅(tryClose 誤回 TOO_FEW，core.exe    */
/*    對同一 raw 4 點也拒絕但理由不同——非「湊不齊 4 點」而是「這個      */
/*    環本身不合法」)，修後綠(NO_CORNER：兩個候選各自都不可行)。        */
/* ---------------------------------------------------------------- */

test("tryClose：G1——補角偏好候選被 existingEdges 擋下、退選候選與草稿既有頂點(0,1000)完全重合 → 攻擊前誤回 TOO_FEW，修後須回 NO_CORNER", () => {
  // F=(0,0)→(0,1000)→(1000,1000)（末段水平）。existingEdges 是一條擋在 x=1000 的
  // 垂直邊，範圍 y∈[200,800]，剛好擋住偏好候選(1000,0)的 L→cand 邊(1000,1000)-(1000,0)
  // （y 範圍重疊 [200,800]），但不擋退選候選(0,1000)的兩段新邊。退選候選(0,1000)
  // 剛好與草稿中段既有頂點完全重合：把它接進環會讓 (0,1000) 在環上出現兩次，形成
  // 「出去又折返」的退化尖刺——GEO-177 版拿「去共線後」的點列判自交，單一 pass 會連坐
  // 吃掉兩側真正的角點(含起點 F=(0,0)），自交檢查在 n<4 時提早放行，讓 tryClose 誤選
  // 這個不可行的候選，最後才在 TOO_FEW 檢查報錯——錯誤碼答非所問(兩個候選其實都不可行，
  // 不是「隨便選一個閉合但頂點不夠」)。GEO-178 起改在 raw 環上判(ringGeometryError)：
  // 收尾段 (0,1000)→(0,0) 與首段 (0,0)→(0,1000) 共線同側、且 L→cand 壓過中段邊，
  // 兩條規則各自都直接判死這個候選，不必再靠「湊不齊 4 點」這個間接跡象。
  const o = baseOpts({ snapOn: false });
  const ext = [[[1000, 200], [1000, 800]]];
  let s = PD.createState();
  const pts = [[0, 0], [0, 1000], [1000, 1000]];
  for (const p of pts) {
    const r = PD.place(s, p, Object.assign({}, o, { existingEdges: ext }));
    assert.strictEqual(r.error, null, "攻擊腳本的落點本身不應被 place() 擋下：" + JSON.stringify(p));
    s = r.state;
  }
  assert.deepStrictEqual(s.pts, pts);
  const r = PD.tryClose(s, { existingEdges: ext });
  assert.strictEqual(r.ok, false, "G1：兩個補角候選都不可行，tryClose 不應回 ok:true");
  assert.strictEqual(r.error && r.error.code, "NO_CORNER",
    "G1：修復後應回 NO_CORNER（退選候選與既有頂點重合、去共線後湊不齊 4 點），" +
    "而非誤報成 TOO_FEW；實際：" + JSON.stringify(r.error));
});

test("tryClose：補角候選與既有頂點重合、但另一候選可行 → 應正常 ok 閉合（正向對照，確認 G1 修復沒有把合法情況也擋掉）", () => {
  // 草稿 (0,0)→(0,600)→(400,600)→(400,1200)→(900,1200)→(900,600)：末段垂直 →
  // 偏好候選 index1=[F.x,L.y]=(0,600)，剛好與草稿中段既有頂點 (0,600) 完全重合
  // （把它接進環會讓 (0,600) 在環上出現兩次，且收尾段 (900,600)→(0,600) 會壓過
  // 中段邊 (0,600)-(400,600)）→ 不可行。退選候選 index0=[L.x,F.y]=(900,0) 是全新
  // 座標，且 L→cand 與末段共線但朝相反側（只共享 L 這一點）→ 可行，L 變成共線贅點
  // 被化簡掉，形狀不變（assertShapePreserved 會逐條驗）。
  const o = baseOpts({ snapOn: false, existingEdges: [] });
  let s = PD.createState();
  const pts = [[0, 0], [0, 600], [400, 600], [400, 1200], [900, 1200], [900, 600]];
  for (const p of pts) {
    const r = PD.place(s, p, o);
    assert.strictEqual(r.error, null, "路徑本身不應被 place() 擋下：" + JSON.stringify(p));
    s = r.state;
  }
  const cc = PD.computeCornerCandidates(s.pts);
  assert.deepStrictEqual(cc.candidates[cc.preferred], [0, 600],
    "本測試前提：偏好候選必須正是與既有頂點 (0,600) 重合的那個，才有測到退選路徑");
  const r = tryCloseChecked(s, { existingEdges: [] }, "G1 正向對照");
  assert.strictEqual(r.ok, true, "偏好候選不可行時應退選到另一個可行候選，不應整體判死");
  assert.ok(r.pts.some(p => p[0] === 900 && p[1] === 0), "應使用退選候選 (900,0) 收尾");
  assert.strictEqual(r.pts.length, 6);
  assert.ok(!r.pts.some(p => p[0] === 900 && p[1] === 600),
    "L=(900,600) 因與收尾段共線而被去共線移除，屬預期行為（它仍落在輸出的邊上）");
});

/* ---------------------------------------------------------------- */
/* W. 對抗審查攻擊腳本逐字回歸（GEO-178）                              */
/*    五個腳本原文在 scratchpad/clarify/：attack1.js attack2.js        */
/*    attack_dup.js attack_g1_padded.js attack_g3.js。以下逐字重現其     */
/*    落點序列與呼叫方式，並補上與 core.exe 的對照結論（scene 檔        */
/*    bug1/bug2/dup_raw/g3_raw/g3_deduped 已實跑，見各測試註解）。      */
/*    U/V 兩段已涵蓋 attack1/attack2/attack_dup，這裡補另外兩個。       */
/* ---------------------------------------------------------------- */

test("W：attack_g1_padded——偏好候選與既有頂點重合、退選候選合法 → ok，且形狀必須守恆", () => {
  const o = baseOpts({ snapOn: false, existingEdges: [] });
  let s = PD.createState();
  for (const p of [[0, 0], [0, 1000], [500, 1000], [500, 1600], [1200, 1600], [1200, 1000]]) {
    const r = PD.place(s, p, o);
    assert.strictEqual(r.error, null, "place rejected " + JSON.stringify(p));
    s = r.state;
  }
  // 偏好候選 (0,1000)(末段垂直→index1)與草稿頂點 (0,1000) 重合、且收尾段會壓過
  // (0,1000)-(500,1000) → 不可行；退選候選 (1200,0) 合法。core.exe 對輸出
  // 「0,0 0,1000 500,1000 500,1600 1200,1600 1200,0」與對應 raw 環都 ACCEPT。
  const r = tryCloseChecked(s, { existingEdges: [] }, "attack_g1_padded");
  assert.strictEqual(r.ok, true);
  assert.deepStrictEqual(r.pts,
    [[0, 0], [0, 1000], [500, 1000], [500, 1600], [1200, 1600], [1200, 0]]);
});

test("W：attack_g3——applyTypedLength 繞過檢查把自交點塞進草稿（G3/G4 根因）→ 修後必須擋下，" +
  "且草稿停在 4 點、後續閉合走合法的退選候選", () => {
  const o = baseOpts({ snapOn: false, existingEdges: [] });
  let s = PD.createState();
  for (const p of [[0, 0], [0, 600], [800, 600], [800, 300]]) {
    const r = PD.place(s, p, o);
    assert.strictEqual(r.error, null, "place rejected " + JSON.stringify(p));
    s = r.state;
  }
  s = Object.assign({}, s, { cur: [-100, 300], typed: "800" });   // 方向 -x、typed 800
  const r2 = PD.applyTypedLength(s, {});
  assert.strictEqual(r2.error && r2.error.code, "CROSS",
    "修前：error 為 null 且 (0,300) 真的落點；修後必須 CROSS");
  assert.deepStrictEqual(r2.state.pts, [[0, 0], [0, 600], [800, 600], [800, 300]],
    "被擋下就不准動 pts");
  // 修前：tryClose 對 5 點草稿回 ok:true、pts=[[0,600],[800,600],[800,300],[0,300]]
  //       ——F=(0,0) 連同整個突出段被去共線吃掉，送出使用者沒畫的矩形。
  //       core.exe:raw 5 點(g3_raw.scene) REJECT、deduped 4 點(g3_deduped.scene) ACCEPT。
  // 修後：草稿停在 4 點，tryClose 走補角退選候選 (800,0)，輸出與 raw 環 core.exe 皆 ACCEPT。
  const r = tryCloseChecked(r2.state, { existingEdges: [] }, "attack_g3");
  assert.strictEqual(r.ok, true);
  assert.deepStrictEqual(r.pts, [[0, 0], [0, 600], [800, 600], [800, 0]]);
});

/* ---------------------------------------------------------------- */
/* S. Esc 階梯純狀態部分                                             */
/* ---------------------------------------------------------------- */

test("Esc 第一層（typed 非空）：只清 typed，pts 不變", () => {
  let s = PD.createState();
  s.pts = [[0, 0], [500, 0]];
  s = PD.typeDigit(s, "3");
  const after = PD.clearTyped(s);
  assert.strictEqual(after.typed, "");
  assert.deepStrictEqual(after.pts, [[0, 0], [500, 0]]);
});

test("Esc 第二層（typed 已空、pts 非空）：清整份草稿 = 回到 createState()", () => {
  let s = PD.createState();
  s.pts = [[0, 0], [500, 0]];
  // 呼叫端在此層直接捨棄 state、換成全新的
  const fresh = PD.createState();
  assert.deepStrictEqual(fresh, { pts: [], cur: null, typed: "", closeReady: false, error: null });
});

/* ---------------------------------------------------------------- */
/* T. 額外狀態轉移覆蓋：頂點吸附落點                                   */
/* ---------------------------------------------------------------- */

test("place：候選點落在既有頂點 ±vertexSnapPx/zoom 內 → 吸附到該頂點座標", () => {
  // 原版場景（從 (1000,0) 沿 x 軸回頭到接近 (0,0)）在正確的軸鎖/BACKTRACK 判定下
  // 其實會被判成回頭（|dx| 遠大於 |dy| 時軸鎖鎖住自由軸=x，落點會落回起點所在的同一條
  // 水平線、方向與第一段相反），不是原註解設想的「往上走」。改用會產生新轉角的情境：
  // (0,0)→(1000,0)→(1000,800)（末段垂直），新一段鎖到 y=800（水平),freePt.x=3 接近
  // 既有頂點 x=0（來自起點),應吸附成 (0,800)。
  let s = PD.createState();
  const o = baseOpts({ snapOn: false, vertexSnapPx: 8, zoom: 1 });
  s = PD.place(s, [0, 0], o).state;
  s = PD.place(s, [1000, 0], o).state;
  s = PD.place(s, [1000, 800], o).state;
  // 從 (1000,800) 出發：freePt=[3,810]，|dx|=997 >= |dy|=10 → 軸鎖鎖 y=800(水平段),
  // x 取自由值 3,接近既有頂點 x=0(誤差 3<=8)應吸附成 0。
  const r = PD.place(s, [3, 810], o);
  assert.strictEqual(r.error, null);
  const last = r.state.pts[r.state.pts.length - 1];
  assert.strictEqual(last[0], 0);   // x 吸附到起點的 x=0（在 ±8 內）
  assert.strictEqual(last[1], 800); // y 軸鎖鎖定在末段高度
});

/* ================================================================ */
/* Z. 跨層裁判：隨機正交草稿 vs core.exe（驗收條件 2）                  */
/* ================================================================ */

function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* 產生保證單純（不自交）的樓梯狀正交多邊形：x、y 沿途只增不減，
   最後一段直接跳回 x=0 收尾，與起點同 x 軸、免補角。 */
function randomStaircasePolygon(rng, minSteps, maxSteps) {
  const steps = minSteps + Math.floor(rng() * (maxSteps - minSteps + 1));
  const pts = [[0, 0]];
  let x = 0, y = 0;
  for (let i = 0; i < steps; ++i) {
    const dx = 100 * (2 + Math.floor(rng() * 8));   // 200..900，100 的倍數
    x += dx;
    pts.push([x, y]);
    const dy = 100 * (2 + Math.floor(rng() * 8));
    y += dy;
    pts.push([x, y]);
  }
  pts.push([0, y]);
  return pts;
}

/* 產生一個會與既有邊相交的「未補正」嘗試：先走三段直角，
   再刻意往回下探、穿過第一段。回傳 { drawn, rejected }：
   drawn 是 place() 實際接受的已定頂點，rejected 是被 CROSS 擋下的候選點。 */
function randomCrossingAttempt(rng, scale) {
  const s0 = scale * (3 + Math.floor(rng() * 5));   // 3..7 倍 scale
  const s1 = scale * (3 + Math.floor(rng() * 5));
  /* 縮回來的 x，必須嚴格 < s0(留至少 1 個 scale 的差距)才能讓 edge2 非零長、
     且下探段確實穿過 edge0——原版 s2 與 s0 各自獨立取隨機值，偶爾會抽出 s2===s0，
     此時 edge2 端點與前一點重合，place() 依規格(見 I 段「候選點與末點重合→忽略」)
     會靜默吃掉該次落點,L 形草稿退化成一條直線,导致下探段變成沿 edge1 回頭的
     BACKTRACK 而非跨越 edge0 的 CROSS——不是本模組的錯,是產生器邊界情況沒夾住。 */
  const s2 = Math.min(s0 - scale, scale * (2 + Math.floor(rng() * 4)));
  const opts = baseOpts({ snapOn: false });
  let st = PD.createState();
  st = PD.place(st, [0, 0], opts).state;
  st = PD.place(st, [s0, 0], opts).state;      // edge0：(0,0)-(s0,0)
  st = PD.place(st, [s0, s1], opts).state;     // edge1：(s0,0)-(s0,s1)
  st = PD.place(st, [s2, s1], opts).state;     // edge2：(s0,s1)-(s2,s1)，s2<s0
  const candidate = [s2, -Math.max(50, Math.floor(scale / 2))]; // 垂直下探，跨过 y=0 的 edge0
  const res = PD.place(st, candidate, opts);
  return { drawn: st.pts, rejected: candidate, placeResult: res };
}

function vertsStr(pts) {
  return pts.map(p => `${p[0]},${p[1]}`).join(" ");
}

function findCoreExe() {
  const tempDir = process.env.TEMP || process.env.TMP || os.tmpdir();
  const p = process.env.GEOMETRY_TEST_CORE || path.join(tempDir, "geometry-tests",
    process.platform === "win32" ? "core.exe" : "core");
  if (!fs.existsSync(p)) {
    throw new Error("找不到核心程式：" + p + "（跨層裁判需要它已建置；可設 GEOMETRY_TEST_CORE）");
  }
  return p;
}

function runCoreOnOutline(coreExe, sceneDir, name, pts) {
  const scenePath = path.join(sceneDir, name + ".scene");
  const line = `surface 1 origin 0 0 2500 u +x v +y outline ${vertsStr(pts)}\n`;
  fs.writeFileSync(scenePath, line, "utf8");
  const maxAttempts = 3;
  for (let attempt = 1; attempt <= maxAttempts; ++attempt) {
    try {
      execFileSync(coreExe, ["--scene", scenePath], { stdio: ["ignore", "pipe", "pipe"] });
      return { accepted: true };
    } catch (e) {
      const stderrText = (e.stderr || "").toString();
      /* Smart App Control 偶爾會擋新編/未快取簽章的 exe（WinError 4551），
         而非真正的幾何拒絕；等 15 秒重試,不視為「核心拒絕」。 */
      const looksLikeSAC = /4551|應用程式控制原則|Smart App Control/i.test(stderrText) ||
        (e.status === null && attempt < maxAttempts);
      if (looksLikeSAC && attempt < maxAttempts) {
        const until = Date.now() + 15000;
        while (Date.now() < until) { /* 忙等，避免依賴額外套件 */ }
        continue;
      }
      return { accepted: false, stderr: stderrText, status: e.status };
    }
  }
  return { accepted: false, stderr: "重試耗盡", status: null };
}

test("跨層裁判：≥200 個隨機正交草稿，tryClose 成功者核心必接受、CROSS 拒絕者核心也拒絕（前端先驗與核心規則一致）", { timeout: 300000 }, () => {
  const coreExe = findCoreExe();
  const sceneDir = fs.mkdtempSync(path.join(os.tmpdir(), "polydraft-judge-"));

  let generated = 0, acceptedByCore = 0, rejectedByCore = 0;
  const mismatches = [];

  /* (a) 140 個應該成功閉合、核心必接受的樓梯狀正交多邊形 */
  for (let i = 0; i < 140; ++i) {
    const rng = mulberry32(1000 + i);
    const raw = randomStaircasePolygon(rng, 2, 5);
    let st = PD.createState();
    const opts = baseOpts({ snapOn: true, gridMm: 100 });
    for (const p of raw.slice(1)) {   // raw[0] 是起點,用第一次 place 落下
      if (st.pts.length === 0) { st = PD.place(st, raw[0], opts).state; continue; }
    }
    // 用 place() 依序落下每一点（含起点）
    st = PD.createState();
    for (const p of raw) {
      const r = PD.place(st, p, opts);
      assert.strictEqual(r.error, null, "樓梯狀草稿不應觸發 CROSS/BACKTRACK：" + JSON.stringify(p));
      st = r.state;
    }
    const closed = tryCloseChecked(st, { existingEdges: [] }, "樓梯_" + i);
    assert.strictEqual(closed.ok, true, "樓梯狀多邊形應可成功閉合：" + JSON.stringify(raw));
    generated++;
    const outcome = runCoreOnOutline(coreExe, sceneDir, "accept_" + i, closed.pts);
    if (!outcome.accepted) {
      mismatches.push({ kind: "should-accept", i, pts: closed.pts, stderr: outcome.stderr });
    } else {
      acceptedByCore++;
    }
  }

  /* (b) 70 個刻意交叉、被 place() CROSS 擋下的嘗試；未補正的多邊形送核心，核心也必須拒絕 */
  for (let i = 0; i < 70; ++i) {
    const rng = mulberry32(9000 + i);
    const scale = 50 * (1 + Math.floor(rng() * 6));   // 50..300
    const { drawn, rejected, placeResult } = randomCrossingAttempt(rng, scale);
    assert.strictEqual(placeResult.error && placeResult.error.code, "CROSS",
      "刻意設計的下探段應被 place() 判為 CROSS：scale=" + scale);
    generated++;
    const uncorrected = drawn.concat([rejected]);
    const outcome = runCoreOnOutline(coreExe, sceneDir, "reject_" + i, uncorrected);
    if (outcome.accepted) {
      mismatches.push({ kind: "should-reject", i, pts: uncorrected });
    } else {
      rejectedByCore++;
    }
  }

  const total = acceptedByCore + rejectedByCore;
  const agreementRate = generated ? (total / generated) : 0;

  console.log(`[跨層裁判] 產生 ${generated} 個草稿；核心接受 ${acceptedByCore} 個（應接受 140 個）；` +
    `核心拒絕 ${rejectedByCore} 個（應拒絕 70 個）；一致率 ${(agreementRate * 100).toFixed(1)}%`);
  if (mismatches.length) {
    console.log("[跨層裁判] 不一致案例（前 5 筆）：",
      JSON.stringify(mismatches.slice(0, 5), null, 2));
  }

  assert.strictEqual(mismatches.length, 0, `跨層裁判出現 ${mismatches.length} 個不一致案例`);
  assert.strictEqual(generated >= 200, true, "至少要產生 200 個草稿");
  assert.strictEqual(acceptedByCore, 140);
  assert.strictEqual(rejectedByCore, 70);

  fs.rmSync(sceneDir, { recursive: true, force: true });
});

/* ================================================================ */
/* Z2. 新跨層裁判：非單調隨機正交路徑，專打 tryClose 收尾自交（GEO-176） */
/*     上面 Z 段的兩個舊產生器都走不到 tryClose 的收尾/補角路徑                */
/*     （randomStaircasePolygon 只單調遞增、免補角；randomCrossingAttempt   */
/*     的交叉在 place() 增量階段就被擋下，從未進到 tryClose）——這正是        */
/*     對抗審查指出的 F3。以下三個產生器 x、y 皆可增可減，且刻意涵蓋：        */
/*     ①需要補角的、②會在收尾段自交的、③收尾段與首段/末段共線回頭的。        */
/* ================================================================ */

/* 一般非單調隨機正交路徑：每步沿垂直於上一步的軸、隨機正負方向、隨機長度前進，
   用 place() 逐步落點（天然保證路徑本身不自交，因為 place() 每步都會查 CROSS）。
   終點與起點是否同軸（直接閉合 vs 需要補角）純看隨機結果，不刻意篩選。 */
function randomNonMonotonicWalk(rng, minSteps, maxSteps, scale) {
  const steps = minSteps + Math.floor(rng() * (maxSteps - minSteps + 1));
  const opts = baseOpts({ snapOn: false });
  let st = PD.createState();
  st = PD.place(st, [0, 0], opts).state;
  let axisIsX = rng() < 0.5;
  let placed = 1, attempts = 0;
  while (placed < steps && attempts < steps * 8) {
    attempts++;
    const last = st.pts[st.pts.length - 1];
    const dir = rng() < 0.5 ? -1 : 1;
    const len = scale * (1 + Math.floor(rng() * 8));
    const cand = axisIsX ? [last[0] + dir * len, last[1]] : [last[0], last[1] + dir * len];
    const r = PD.place(st, cand, opts);
    if (r.error) continue;   /* 被 CROSS/BACKTRACK 擋下就換個方向/長度重試 */
    st = r.state;
    placed++;
    axisIsX = !axisIsX;
  }
  return st;
}

/* 仿對抗審查 F2 攻擊案例結構（先走一小段、再往一個方向大幅超越、末段與起點不同軸）
   的隨機化版本：大幅超越讓偏好補角候選與草稿中段重疊/相交的機率大增，專門逼近
   NO_CORNER 或「退選到與末段共線」的候選路徑。 */
function randomForcedOverlapCorner(rng, scale) {
  const opts = baseOpts({ snapOn: false });
  const h1 = scale * (2 + Math.floor(rng() * 4));
  const w1 = scale * (2 + Math.floor(rng() * 4));
  const h2 = scale * (8 + Math.floor(rng() * 12));
  const w2 = scale * (8 + Math.floor(rng() * 12));
  const vSign = rng() < 0.5 ? 1 : -1;
  const hSign = rng() < 0.5 ? 1 : -1;
  const endOffset = scale * (1 + Math.floor(rng() * 6)) * (rng() < 0.5 ? 1 : -1);
  let st = PD.createState();
  st = PD.place(st, [0, 0], opts).state;
  const steps = [
    [0, vSign * h1],
    [hSign * w1, vSign * h1],
    [hSign * w1, vSign * h1 - vSign * h2],
    [hSign * (w1 + w2), vSign * h1 - vSign * h2],
    [hSign * (w1 + w2), vSign * h1 - vSign * h2 + endOffset],
  ];
  for (const p of steps) {
    const r = PD.place(st, p, opts);
    if (r.error) return st;   /* 中途被擋就提早結束，回傳已定部分（仍是合法草稿） */
    st = r.state;
  }
  return st;
}

/* 非單調隨機路徑 + 強制末段軸回到與起點同軸（直接閉合，免補角），刻意衝高
   「收尾段與首段共線回頭」（末點/起點在去共線時互相吃掉）的出現機率：先做一段
   一般隨機走位，最後一步把當下該走的軸座標直接歸零，逼出與 F=(0,0) 同軸。若這步
   本身就先被 place() 的 CROSS/BACKTRACK 擋下，直接回傳未補這步的路徑（仍是需要
   補角的合法樣本，不強求）。 */
function randomDirectCloseSeam(rng, minSteps, maxSteps, scale) {
  const st = randomNonMonotonicWalk(rng, minSteps, maxSteps, scale);
  if (st.pts.length < 3) return st;
  const opts = baseOpts({ snapOn: false });
  const last = st.pts[st.pts.length - 1];
  const prevLast = st.pts[st.pts.length - 2];
  const lastAxisIsX = prevLast[1] === last[1];   /* 最後一段是水平 → 下一段該走垂直軸 */
  const nextAxisIsX = !lastAxisIsX;
  const cand = nextAxisIsX ? [0, last[1]] : [last[0], 0];
  const r = PD.place(st, cand, opts);
  return r.error ? st : r.state;
}

/* G2（對抗審查、GEO-177）：實跑 core.exe --scene 對 0 點/1 點/2 點/3 點/自交 4 點/
   零長邊/非軸平行各探過一輪，stderr 只有兩種可能，且都是「結構性拒絕」（不是幾何
   判定以外的失敗）：
     (a) outline 子句一個 u,v 都沒有（去共線後整條環吃到 0 點）→ DSL 解析層擋下：
         「outline 後面要接至少四個 u,v 頂點」
     (b) outline 有 >=1 個 u,v，但送進 poly_loop_is_valid 後不合法（頂點數<4、
         非軸平行、零長邊、自交/共線重疊、shoelace 面積為 0，五種理由共用一句)：
         「邊界面輪廓不合法：邊要軸平行、不零長、不自交；孔要在外輪廓內且互不重疊」
   也就是說 core.exe 本身**不區分** TOO_FEW/CROSS/DEGENERATE——模組錯誤碼 ↔ 核心
   訊息類別沒有能對到「唯一」的細分映射，只有「accept ↔ 這兩句已知 reject 之一」
   這個粗粒度的二元映射。這是實測結果，不是偷懶放寬：與其假裝能對出四類訊息，不如
   把這個粗粒度映射本身驗實——核心「拒絕」還要進一步核對 stderr 真的是這兩句已知的
   結構性理由之一，而不是別的失敗（例如場景 DSL 拼錯、id 衝突等不相干錯誤），避免
   把「core 用不相干的理由剛好也拒絕」誤記成「兩層判定一致」。 */
/* GEO-180 追加第三句已知的結構性拒絕理由:座標超出 COORD_LIMIT 時，場景 DSL 在
   解析數值當下就擋（current_geometry.c:12026），訊息與輪廓不合法那句不同。 */
const CORE_REJECT_REASON_RE =
  /邊界面輪廓不合法|outline 後面要接至少四個 u,v 頂點|座標或尺寸超出支援範圍/;

/* accepted → "accepted"；rejected 且 stderr 命中已知的結構性理由 → "rejected-known"；
   rejected 但理由對不上（場景生成本身有問題，不是幾何判定分歧）→ "rejected-unknown"。 */
function classifyCoreVerdict(outcome) {
  if (outcome.accepted) return "accepted";
  return CORE_REJECT_REASON_RE.test(outcome.stderr || "") ? "rejected-known" : "rejected-unknown";
}

/* 對一個草稿跑 tryClose，並依結果組出「送核心驗證」的候選。
   GEO-178 改動（重要）:一律送 **raw 環**（草稿點列 +（需要時）補角頂點，未去共線），
   因為那正是 tryClose 現在實際驗證的東西（polydraft.js 檔頭原則 2）。GEO-177 版送的是
   去共線後的點列，等於拿模組自己的化簡結果去問核心——core.exe 對同一候選的 raw/deduped
   可能給出相反判定（G3：raw 5 點 REJECT、deduped 4 點 ACCEPT），送 deduped 會讓「化簡
   偷改形狀」這個病在跨層裁判裡剛好被掩蓋掉。
   - ok:true → 送兩筆：tryClose 輸出的 pts、以及對應的 raw 環，核心**兩筆都必須接受**。
     （形狀守恆保證兩者是同一個幾何；若核心對其中一筆說不，就是模組在騙人。）
   - CROSS（只可能來自直接閉合分支）→ 送草稿 raw 環（末點直接接回起點），核心必拒絕。
   - NO_CORNER → 兩個候選各自的 raw 環分別送核心，兩個都必須被拒絕才算一致。
   - TOO_FEW/DEGENERATE → 同樣送草稿 raw 環，核心必拒絕。補角分支的任何不可行候選都
     會被歸成 NO_CORNER（見 polydraft.js::tryClose），所以這兩碼必定來自直接閉合分支；
     這裡直接 assert 這個前提，不再有「跳過不驗」的分支（驗收條件：不得 skip）。
   回傳 { kind, coreVerdicts: [...] }，coreVerdicts 每筆 { accepted, stderr }。 */
function judgeAgainstCore(coreExe, sceneDir, name, st) {
  const closed = PD.tryClose(st, { existingEdges: [] });
  if (closed.ok) {
    assertShapePreserved(st.pts, closed.pts, name);
    const raw = rawRingOf(st.pts, closed.pts);
    return {
      kind: "ok", code: null, coreVerdicts: [
        runCoreOnOutline(coreExe, sceneDir, name + "_ok", closed.pts),
        runCoreOnOutline(coreExe, sceneDir, name + "_ok_raw", raw),
      ],
    };
  }
  const code = closed.error.code;
  const F = st.pts[0], L = st.pts[st.pts.length - 1];
  const needsCorner = !(L[0] === F[0] || L[1] === F[1]);
  if (needsCorner) {
    /* 補角分支的不可行候選一律收斂成 NO_CORNER，唯一的例外是容量問題 TOO_MANY
       （換另一個轉折也救不了，見 polydraft.js::tryClose）。 */
    assert.ok(code === "NO_CORNER" || code === "TOO_MANY",
      `${name}：補角分支只會回 NO_CORNER/TOO_MANY，實際 ${code}`);
    const { candidates } = PD.computeCornerCandidates(st.pts);
    const verdicts = candidates.map((cand, idx) =>
      runCoreOnOutline(coreExe, sceneDir, name + "_corner" + idx, st.pts.concat([cand])));
    return { kind: "reject", code, coreVerdicts: verdicts };
  }
  const outcome = runCoreOnOutline(coreExe, sceneDir, name + "_" + code.toLowerCase(), st.pts);
  return { kind: "reject", code, coreVerdicts: [outcome] };
}

/* G2 補丁的直接驗證（GEO-177）：目前 220 個 GEO-176 產生器族群裡 TOO_FEW/DEGENERATE
   出現次數是 0（見下面大測試印出的統計），代表大測試本身測不到 judgeAgainstCore 這條
   新分支有沒有真的在動。這裡直接拿 P 段「tryClose：去共線後頂點數 <4 → TOO_FEW」同一個
   已知會觸發 TOO_FEW 的場景，繞過大測試的隨機產生器，直接呼叫 judgeAgainstCore 驗證：
   (1) 不再被 kind:"skip" 吞掉、(2) core.exe 真的也拒絕、(3) 拒絕理由命中已知的結構性
   訊息（不是場景生成出錯的巧合拒絕）。 */
test("跨層裁判 G2（GEO-177）：judgeAgainstCore 不再略過 TOO_FEW——3 點共線草稿的 TOO_FEW 也送核心交叉驗證", () => {
  const coreExe = findCoreExe();
  const sceneDir = fs.mkdtempSync(path.join(os.tmpdir(), "polydraft-judge-toofew-"));
  const st = { pts: [[0, 0], [500, 0], [1000, 0]], cur: null, typed: "", closeReady: true, error: null };
  const closed = PD.tryClose(st, { existingEdges: [] });
  assert.strictEqual(closed.error && closed.error.code, "TOO_FEW", "測試前提：這個場景必須真的觸發 TOO_FEW");
  const r = judgeAgainstCore(coreExe, sceneDir, "toofew_sanity", st);
  assert.strictEqual(r.kind, "reject", "GEO-177 修復後 TOO_FEW 不應再被 judgeAgainstCore 跳過");
  assert.strictEqual(r.code, "TOO_FEW");
  assert.strictEqual(r.coreVerdicts.length, 1);
  assert.strictEqual(classifyCoreVerdict(r.coreVerdicts[0]), "rejected-known",
    "core.exe 應該也拒絕這個湊不齊 4 點的環，且理由要命中已知的結構性訊息：" +
    JSON.stringify(r.coreVerdicts[0]));
  fs.rmSync(sceneDir, { recursive: true, force: true });
});

/* 跨層裁判的計數/比對外殼（Z2 與 Z3 共用一份，免得兩邊的判準漂移）:
   run(name, st) 對一個草稿跑 judgeAgainstCore 並把結論歸到四類統計;
   pts.length<3 的過短樣本不判（skipped），其餘一律要判到底，不得 skip。 */
function makeJudgeCollector(coreExe, sceneDir) {
  const J = {
    generated: 0, skipped: 0,
    okCount: 0, crossCount: 0, noCornerCount: 0, tooFewDegenerateCount: 0,
    okAgree: 0, crossAgree: 0, noCornerAgree: 0, tooFewDegenerateAgree: 0,
    mismatches: [],
  };
  J.run = function (name, st) {
    if (st.pts.length < 3) { J.skipped++; return; }
    const r = judgeAgainstCore(coreExe, sceneDir, name, st);
    J.generated++;
    if (r.kind === "ok") {
      J.okCount++;
      /* 輸出點列與 raw 環兩筆都要被核心接受（形狀守恆保證它們是同一個幾何）。 */
      if (r.coreVerdicts.every(v => v.accepted)) J.okAgree++;
      else J.mismatches.push({
        kind: "should-accept", name, pts: PD.tryClose(st, { existingEdges: [] }).pts,
        stderr: r.coreVerdicts.map(v => v.stderr).join(" | "),
      });
    } else if (r.code === "CROSS") {
      J.crossCount++;
      const cls = classifyCoreVerdict(r.coreVerdicts[0]);
      if (cls === "rejected-known") J.crossAgree++;
      else J.mismatches.push({
        kind: cls === "accepted" ? "should-reject-cross" : "cross-rejected-for-unrecognized-reason",
        name, pts: st.pts, stderr: r.coreVerdicts[0].stderr,
      });
    } else if (r.code === "NO_CORNER") {
      J.noCornerCount++;
      const classes = r.coreVerdicts.map(classifyCoreVerdict);
      if (classes.every(c => c === "rejected-known")) J.noCornerAgree++;
      else J.mismatches.push({
        kind: "no-corner-candidate-verdict-mismatch", name, verdicts: r.coreVerdicts, classes,
      });
    } else if (r.code === "TOO_FEW" || r.code === "DEGENERATE" || r.code === "TOO_MANY") {
      J.tooFewDegenerateCount++;
      const classes = r.coreVerdicts.map(classifyCoreVerdict);
      if (classes.every(c => c === "rejected-known")) J.tooFewDegenerateAgree++;
      else J.mismatches.push({
        kind: classes.includes("accepted") ? "should-reject-" + r.code.toLowerCase()
          : r.code.toLowerCase() + "-rejected-for-unrecognized-reason",
        name, code: r.code, pts: st.pts, classes,
        stderr: r.coreVerdicts.map(v => v.stderr).join(" | "),
      });
    } else {
      J.mismatches.push({ kind: "unexpected-code", name, code: r.code });
    }
  };
  J.report = function (label) {
    const agree = J.okAgree + J.crossAgree + J.noCornerAgree + J.tooFewDegenerateAgree;
    const rate = J.generated ? (agree / J.generated) : 0;
    console.log(`[跨層裁判 ${label}] 產生 ${J.generated} 個（略過 ${J.skipped} 個過短樣本）；` +
      `ok=${J.okCount}(核心同意 ${J.okAgree})、CROSS=${J.crossCount}(核心同意 ${J.crossAgree})、` +
      `NO_CORNER=${J.noCornerCount}(核心同意 ${J.noCornerAgree})、` +
      `TOO_FEW+DEGENERATE+TOO_MANY=${J.tooFewDegenerateCount}(核心同意 ${J.tooFewDegenerateAgree})；` +
      `一致率 ${(rate * 100).toFixed(1)}%`);
    if (J.mismatches.length) {
      console.log(`[跨層裁判 ${label}] 不一致案例（前 5 筆）：`,
        JSON.stringify(J.mismatches.slice(0, 5), null, 2));
    }
    return rate;
  };
  return J;
}

test("跨層裁判（GEO-176）：≥200 個非單調隨機正交草稿（含需補角/收尾自交/收尾共線回頭），tryClose 接受者核心必接受、CROSS/NO_CORNER 拒絕者核心也必拒絕", { timeout: 300000 }, () => {
  const coreExe = findCoreExe();
  const sceneDir = fs.mkdtempSync(path.join(os.tmpdir(), "polydraft-judge2-"));

  const J = makeJudgeCollector(coreExe, sceneDir);
  const run = J.run;

  /* (a) 100 個一般非單調隨機路徑：4~9 步，scale 40..300 */
  for (let i = 0; i < 100; ++i) {
    const rng = mulberry32(20000 + i);
    const scale = 40 * (1 + Math.floor(rng() * 8));
    const st = randomNonMonotonicWalk(rng, 4, 9, scale);
    run("walk_" + i, st);
  }

  /* (b) 60 個仿 F2 結構的強制重疊補角路徑：scale 30..150 */
  for (let i = 0; i < 60; ++i) {
    const rng = mulberry32(30000 + i);
    const scale = 30 * (1 + Math.floor(rng() * 5));
    const st = randomForcedOverlapCorner(rng, scale);
    run("overlap_" + i, st);
  }

  /* (c) 60 個強制末段回到與起點同軸（直接閉合）的非單調路徑：scale 40..250 */
  for (let i = 0; i < 60; ++i) {
    const rng = mulberry32(40000 + i);
    const scale = 40 * (1 + Math.floor(rng() * 6));
    const st = randomDirectCloseSeam(rng, 4, 8, scale);
    run("seam_" + i, st);
  }

  J.report("GEO-176");
  assert.strictEqual(J.mismatches.length, 0, `跨層裁判（GEO-176）出現 ${J.mismatches.length} 個不一致案例`);
  assert.strictEqual(J.generated >= 200, true, "至少要產生 200 個非單調隨機草稿");
  /* 三種情境都要有實際出現（見驗收條件 2：需補角/收尾自交/收尾共線回頭都要有比例），
     不能全部落在同一種結局。TOO_FEW/DEGENERATE 不強求出現（見 judgeAgainstCore 註解，
     這兩碼在目前的產生器族群裡本來就極罕見/不可達，GEO-176/177/178 三輪都是 0 次）。 */
  assert.ok(J.crossCount > 0, "應該要有至少一個 CROSS（收尾自交）樣本");
  assert.ok(J.noCornerCount > 0, "應該要有至少一個 NO_CORNER（補角雙候選皆撞）樣本");
  assert.ok(J.okCount > 0, "應該要有至少一個成功閉合樣本");

  fs.rmSync(sceneDir, { recursive: true, force: true });
});

/* ================================================================ */
/* Z3. 跨層裁判：混合 place 與 applyTypedLength 的隨機草稿（GEO-178）   */
/*     Z/Z2 的四個產生器全部只走 place()——applyTypedLength 這條管道     */
/*     從來沒被任何隨機測試碰過，這正是 G3/G4 能成立的原因（純 place    */
/*     序列走不到那個自交點，只有鍵入長度能把它塞進草稿）。這裡每一步    */
/*     隨機選「滑鼠落點」或「鍵入長度」前進，兩條管道產出的草稿送同一套  */
/*     裁判，並統計鍵入長度被 CROSS/BACKTRACK 擋下的次數（>0 才算真的    */
/*     測到新檢查）。                                                  */
/* ================================================================ */

function randomMixedWalk(rng, minSteps, maxSteps, scale, stats) {
  const steps = minSteps + Math.floor(rng() * (maxSteps - minSteps + 1));
  const opts = baseOpts({ snapOn: false });
  let st = PD.createState();
  st = PD.place(st, [0, 0], opts).state;
  let axisIsX = rng() < 0.5;
  let placed = 1, attempts = 0;
  while (placed < steps && attempts < steps * 8) {
    attempts++;
    const last = st.pts[st.pts.length - 1];
    const dir = rng() < 0.5 ? -1 : 1;
    const len = scale * (1 + Math.floor(rng() * 8));
    if (rng() < 0.5) {
      /* 鍵入長度：方向由 state.cur 相對末點決定，呼叫端負責先把 cur 寫回 state
         （POLYDRAFT-API §3 / app.js::objPolyPreviewMove），這裡用一個離末點 10mm
         的同向點當游標位置。 */
      const cur = axisIsX ? [last[0] + dir * 10, last[1]] : [last[0], last[1] + dir * 10];
      const typedState = Object.assign({}, st, { cur, typed: String(len) });
      const r = PD.applyTypedLength(typedState, { existingEdges: [] });
      if (r.error) {
        stats.typedRejected[r.error.code] = (stats.typedRejected[r.error.code] || 0) + 1;
        continue;   /* 被擋下就換方向/長度重試，與 place 分支同樣的重試策略 */
      }
      if (r.state === typedState) continue;   /* 重合被忽略（len 不會是 0，防禦） */
      stats.typedSteps++;
      st = r.state;
    } else {
      const cand = axisIsX ? [last[0] + dir * len, last[1]] : [last[0], last[1] + dir * len];
      const r = PD.place(st, cand, opts);
      if (r.error) {
        stats.placeRejected[r.error.code] = (stats.placeRejected[r.error.code] || 0) + 1;
        continue;
      }
      stats.placeSteps++;
      st = r.state;
    }
    placed++;
    /* 85% 換軸（正交多邊形的正常走法）；15% 故意留在同一軸 → 下一步不是共線延長
       就是沿原邊回頭，用來把 extend / BACKTRACK 兩條路徑也掃到（兩條管道都要掃）。 */
    if (rng() < 0.85) axisIsX = !axisIsX;
  }
  return st;
}

test("跨層裁判（GEO-178）：≥120 個混合 place/applyTypedLength 的隨機正交草稿，兩條落點管道受同一套規則約束，" +
  "tryClose 接受者核心必接受（輸出與 raw 環各一筆）、拒絕者核心也必拒絕", { timeout: 300000 }, () => {
  const coreExe = findCoreExe();
  const sceneDir = fs.mkdtempSync(path.join(os.tmpdir(), "polydraft-judge3-"));
  const J = makeJudgeCollector(coreExe, sceneDir);
  const stats = { typedSteps: 0, placeSteps: 0, typedRejected: {}, placeRejected: {} };

  for (let i = 0; i < 120; ++i) {
    const rng = mulberry32(60000 + i);
    const scale = 40 * (1 + Math.floor(rng() * 6));   // 40..240
    const st = randomMixedWalk(rng, 4, 9, scale, stats);
    J.run("mixed_" + i, st);
  }

  J.report("GEO-178 混合管道");
  console.log(`[跨層裁判 GEO-178] 落點管道統計：applyTypedLength 成功 ${stats.typedSteps} 步` +
    `（被擋 ${JSON.stringify(stats.typedRejected)}）、place 成功 ${stats.placeSteps} 步` +
    `（被擋 ${JSON.stringify(stats.placeRejected)}）`);

  assert.strictEqual(J.mismatches.length, 0, `跨層裁判（GEO-178）出現 ${J.mismatches.length} 個不一致案例`);
  assert.ok(J.generated >= 100, "至少要有 100 個可判樣本");
  assert.ok(stats.typedSteps > 0, "產生器必須真的有走到 applyTypedLength");
  assert.ok((stats.typedRejected.CROSS || 0) + (stats.typedRejected.BACKTRACK || 0) > 0,
    "必須有 applyTypedLength 被 CROSS/BACKTRACK 擋下的實例，否則 GEO-178 的新檢查沒被測到：" +
    JSON.stringify(stats.typedRejected));
  assert.ok(J.okCount > 0, "應該要有至少一個成功閉合樣本");

  fs.rmSync(sceneDir, { recursive: true, force: true });
});

/* ================================================================ */
/* Y. 頂點上限 POLY_MAX_VERTICES（GEO-179）                            */
/*    核心 current_geometry.c 的上限是 32，兩處各自擋:                 */
/*      :198  #define POLY_MAX_VERTICES 32                           */
/*      :229-232 poly_loop_is_valid：count<4 或 count>32 → 不合法      */
/*      :8487-8489 parse_loop_vertices：讀到第 33 個 u,v 直接 return -1 */
/*                （呼叫端 :8568-8574 報「outline 後面要接至少四個 u,v  */
/*                 頂點」——同一句話兼管太少與太多）                    */
/*    前端先驗必須在落點當下就擋，不能畫到第 33 點才在送核心時被打回。   */
/* ================================================================ */

/* 垂直起步的樓梯草稿：P0=(0,0) 先往上，之後交錯「右、上」，共 1+2k 個點。
   末點與起點不同軸 → 需要補角，補角點 (X_k, 0) 讓輸出剛好 2k+2 個頂點；
   withDirectClose=true 則自己補上 (X_k,0) 當最後一個草稿點 → 免補角，輸出同樣 2k+2。
   （正交簡單環的頂點數恆為偶數：邊必須橫直交錯，奇數條邊繞不回來。） */
function verticalStaircaseDraft(k, step, withDirectClose) {
  const pts = [[0, 0]];
  let x = 0;
  for (let i = 1; i <= k; ++i) {
    pts.push([x, i * step]);        // 垂直往上
    x = 2 * i * step;               // 嚴格遞增的 X_i
    pts.push([x, i * step]);        // 水平往右
  }
  if (withDirectClose) pts.push([x, 0]);
  return pts;
}

function placeAll(pts, opts) {
  let s = PD.createState();
  for (const p of pts) {
    const r = PD.place(s, p, opts);
    assert.strictEqual(r.error, null, "草稿應可逐點畫出：" + JSON.stringify(p) +
      " 實際：" + JSON.stringify(r.error));
    s = r.state;
  }
  return s;
}

test("place：草稿已達核心上限 32 個頂點 → 第 33 點回 TOO_MANY、草稿不變（共線延長不受限）", () => {
  const o = baseOpts({ snapOn: false, existingEdges: [] });
  const draft = verticalStaircaseDraft(15, 100, true);
  assert.strictEqual(draft.length, 32, "測試前提：這個樓梯草稿剛好 32 點");
  const s = placeAll(draft, o);
  assert.strictEqual(s.pts.length, 32);

  // (2900,0) 幾何上完全合法（y=0 那條線上只有起點附近的 e0，x 到不了 0），純粹是第 33 點。
  const r = PD.place(s, [2900, 0], o);
  assert.strictEqual(r.error && r.error.code, "TOO_MANY",
    "第 33 點必須在落點當下就被擋下；實際：" + JSON.stringify(r.error));
  assert.strictEqual(r.state, s, "被擋下就不准動草稿");

  // 共線延長不會增加頂點數 → 即使已達上限也必須放行（擋的是「頂點數」不是「落點」）。
  const ext = PD.place(s, [3000, -500], o);
  assert.strictEqual(ext.error, null, "共線延長不新增頂點,不該被上限擋下");
  assert.strictEqual(ext.state.pts.length, 32);
});

test("applyTypedLength：草稿已達 32 點 → 鍵入長度的新段同樣回 TOO_MANY（兩條管道同一道檢查）", () => {
  const o = baseOpts({ snapOn: false, existingEdges: [] });
  const s = placeAll(verticalStaircaseDraft(15, 100, true), o);
  const typedState = Object.assign({}, s, { cur: [2990, 0], typed: "100" });
  const r = PD.applyTypedLength(typedState, { existingEdges: [] });
  assert.strictEqual(r.error && r.error.code, "TOO_MANY");
  assert.strictEqual(r.state, typedState);
});

test("tryClose：草稿 33 點、補角後 34 個頂點 → TOO_MANY（先於送核心擋下，不是 NO_CORNER）", () => {
  const pts = verticalStaircaseDraft(16, 100, false);
  assert.strictEqual(pts.length, 33, "測試前提：33 點草稿（只能由未經 place 的呼叫端傳入）");
  const r = PD.tryClose({ pts, cur: null, typed: "", closeReady: true, error: null },
    { existingEdges: [] });
  assert.strictEqual(r.ok, false);
  assert.strictEqual(r.error.code, "TOO_MANY",
    "候選本身是合法幾何,唯一的問題是頂點數超過核心上限,錯誤碼不該被收斂成 NO_CORNER");
});

test("tryClose：草稿 34 點、免補角直接閉合 → TOO_MANY", () => {
  const pts = verticalStaircaseDraft(16, 100, true);
  assert.strictEqual(pts.length, 34);
  const r = PD.tryClose({ pts, cur: null, typed: "", closeReady: true, error: null },
    { existingEdges: [] });
  assert.strictEqual(r.ok, false);
  assert.strictEqual(r.error.code, "TOO_MANY");
});

test("tryClose：草稿 31 點 + 補角 = 剛好 32 個頂點（上限邊界內）→ 正常 ok", () => {
  const o = baseOpts({ snapOn: false, existingEdges: [] });
  const s = placeAll(verticalStaircaseDraft(15, 100, false), o);
  assert.strictEqual(s.pts.length, 31);
  const r = tryCloseChecked(s, { existingEdges: [] }, "上限邊界-補角");
  assert.strictEqual(r.ok, true, "剛好踩在上限上要放行；實際：" + JSON.stringify(r.error));
  assert.strictEqual(r.pts.length, 32);
});

test("跨層裁判（GEO-179）：頂點上限不是背常數——32 點 outline 核心必接受、34 點與 33 點 outline 核心必拒絕", { timeout: 120000 }, () => {
  const coreExe = findCoreExe();
  const sceneDir = fs.mkdtempSync(path.join(os.tmpdir(), "polydraft-judge-cap-"));
  const o = baseOpts({ snapOn: false, existingEdges: [] });

  // (c) 恰好 32 點、免補角:模組回 ok，核心必須接受（形狀守恆斷言一併跑）。
  const s32 = placeAll(verticalStaircaseDraft(15, 100, true), o);
  const closed = tryCloseChecked(s32, { existingEdges: [] }, "cap32");
  assert.strictEqual(closed.ok, true);
  assert.strictEqual(closed.pts.length, 32);
  const v32 = runCoreOnOutline(coreExe, sceneDir, "cap_32", closed.pts);
  assert.strictEqual(classifyCoreVerdict(v32), "accepted",
    "32 個頂點的合法正交環核心必須接受：" + JSON.stringify(v32));

  // (d) 34 點:同一族形狀、幾何一樣乾淨，只是多了兩個頂點 → 核心必須拒絕（證明擋的是上限）。
  const ring34 = verticalStaircaseDraft(16, 100, true);
  assert.strictEqual(ring34.length, 34);
  const v34 = runCoreOnOutline(coreExe, sceneDir, "cap_34", ring34);
  assert.strictEqual(classifyCoreVerdict(v34), "rejected-known",
    "34 個頂點必須被核心拒絕（POLY_MAX_VERTICES=32）：" + JSON.stringify(v34));

  // 33 個 u,v 的 outline:解析層讀到第 33 個就 return -1（current_geometry.c:8487）。
  const v33 = runCoreOnOutline(coreExe, sceneDir, "cap_33", ring34.slice(0, 33));
  assert.strictEqual(classifyCoreVerdict(v33), "rejected-known",
    "33 個 u,v 的 outline 必須被核心拒絕：" + JSON.stringify(v33));

  console.log(`[跨層裁判 GEO-179] 上限實測:32 點 → ${v32.accepted ? "ACCEPT" : "REJECT"}、` +
    `33 點 → ${v33.accepted ? "ACCEPT" : "REJECT"}、34 點 → ${v34.accepted ? "ACCEPT" : "REJECT"}` +
    `（核心 POLY_MAX_VERTICES=32，current_geometry.c:198/:229-232/:8487）`);

  fs.rmSync(sceneDir, { recursive: true, force: true });
});

/* ================================================================ */
/* X. 座標範圍 COORD_LIMIT（對抗審查 H1，GEO-180）                     */
/*    核心 current_geometry.c:43-47                                  */
/*      #define COORD_LIMIT INT64_C(100000000)                      */
/*      coord_in_range(v) = (v >= -COORD_LIMIT && v <= COORD_LIMIT)  */
/*      → 兩端都**含**等號（±1e8 本身合法）                           */
/*    :239 poly_loop_is_valid 對環上**每一個頂點**呼叫 coord_in_range; */
/*    場景 DSL 另有一道 :12026「座標或尺寸超出支援範圍（-100000000 至   */
/*    100000000 mm）」。攻擊腳本 attack_coordlimit.js:模組全不驗範圍， */
/*    place 四點全收、tryClose ok:true，同一 outline core.exe 拒絕。   */
/*    邊界不背常數:下面的跨層測試用 core.exe 實測定邊界。              */
/* ================================================================ */

const COORD_LIMIT_EXPECTED = 100000000;

test("X：attack_coordlimit 逐字回歸——place 第二點座標 2e8 超界 → OUT_OF_RANGE、草稿不變", () => {
  const o = baseOpts({ snapOn: false, existingEdges: [] });
  let s = PD.createState();
  s = PD.place(s, [0, 0], o).state;
  const r = PD.place(s, [200000000, 0], o);
  assert.strictEqual(r.error && r.error.code, "OUT_OF_RANGE",
    "修前 place 全收、tryClose 回 ok:true,core.exe 卻拒絕同一個 outline；實際：" +
    JSON.stringify(r.error));
  assert.strictEqual(r.state, s, "被擋下就不准動草稿");
  assert.strictEqual(s.pts.length, 1);
});

test("X：place 的第一點就超界 → OUT_OF_RANGE（首點分支不經 evaluateNextPoint，要另外擋）", () => {
  const o = baseOpts({ snapOn: false, existingEdges: [] });
  const r = PD.place(PD.createState(), [0, -200000000], o);
  assert.strictEqual(r.error && r.error.code, "OUT_OF_RANGE");
  assert.deepStrictEqual(r.state.pts, []);
});

test("X：applyTypedLength 算出的新點超界 → OUT_OF_RANGE、草稿不變", () => {
  const st = {
    pts: [[0, 0], [99999000, 0]], cur: [99999100, 0], typed: "2000",
    closeReady: false, error: null,
  };
  const r = PD.applyTypedLength(st, { existingEdges: [] });
  assert.strictEqual(r.error && r.error.code, "OUT_OF_RANGE",
    "99999000+2000 = 100001000 > 1e8；實際：" + JSON.stringify(r.error));
  assert.strictEqual(r.state, st);
});

test("X：tryClose 對超界草稿（未經 place 的呼叫端）→ OUT_OF_RANGE，直接閉合與補角兩個分支都要擋", () => {
  const direct = [[0, 0], [200000000, 0], [200000000, 500], [0, 500]];   // F/L 同軸 → 直接閉合
  const r1 = PD.tryClose({ pts: direct, cur: null, typed: "", closeReady: true, error: null },
    { existingEdges: [] });
  assert.strictEqual(r1.ok, false, "attack_coordlimit 的 tryClose 修前回 ok:true");
  assert.strictEqual(r1.error.code, "OUT_OF_RANGE");

  const corner = [[0, 0], [200000000, 0], [200000000, 500]];             // F/L 不同軸 → 補角
  const r2 = PD.tryClose({ pts: corner, cur: null, typed: "", closeReady: true, error: null },
    { existingEdges: [] });
  assert.strictEqual(r2.ok, false);
  assert.strictEqual(r2.error.code, "OUT_OF_RANGE",
    "座標超界換另一個轉折也救不了,不該收斂成 NO_CORNER；實際：" + JSON.stringify(r2.error));
});

test("跨層裁判（GEO-180）：座標邊界由 core.exe 實測決定——恰為上下限的矩形核心接受且模組放行、" +
  "超出一單位核心拒絕且模組擋下", { timeout: 120000 }, () => {
  const coreExe = findCoreExe();
  const sceneDir = fs.mkdtempSync(path.join(os.tmpdir(), "polydraft-judge-coord-"));
  const o = baseOpts({ snapOn: false, existingEdges: [] });

  /* 先用 core.exe 量出邊界,不背常數:同一個矩形，只把 x 從 L 改成 L+1。 */
  const ringAt = (x) => [[0, 0], [x, 0], [x, 500], [0, 500]];
  const L = COORD_LIMIT_EXPECTED;
  const atLimit = runCoreOnOutline(coreExe, sceneDir, "coord_at", ringAt(L));
  const overLimit = runCoreOnOutline(coreExe, sceneDir, "coord_over", ringAt(L + 1));
  const atLower = runCoreOnOutline(coreExe, sceneDir, "coord_at_neg",
    [[-L, 0], [0, 0], [0, 500], [-L, 500]]);
  const overLower = runCoreOnOutline(coreExe, sceneDir, "coord_over_neg",
    [[-L - 1, 0], [0, 0], [0, 500], [-L - 1, 500]]);

  assert.strictEqual(classifyCoreVerdict(atLimit), "accepted",
    `核心應接受座標恰為 ${L} 的矩形（邊界含等號）：` + JSON.stringify(atLimit));
  assert.strictEqual(classifyCoreVerdict(atLower), "accepted",
    `核心應接受座標恰為 -${L} 的矩形：` + JSON.stringify(atLower));
  assert.strictEqual(classifyCoreVerdict(overLimit), "rejected-known",
    `核心應拒絕 ${L + 1}：` + JSON.stringify(overLimit));
  assert.strictEqual(classifyCoreVerdict(overLower), "rejected-known",
    `核心應拒絕 -${L + 1}：` + JSON.stringify(overLower));

  /* 模組必須與這個實測邊界逐點對齊。 */
  let s = PD.createState();
  for (const p of ringAt(L)) {
    const r = PD.place(s, p, o);
    assert.strictEqual(r.error, null, "恰為上限的座標必須放行：" + JSON.stringify(p));
    s = r.state;
  }
  const closed = tryCloseChecked(s, { existingEdges: [] }, "coord_at_limit");
  assert.strictEqual(closed.ok, true, "恰為上限的矩形模組要能閉合");
  assert.deepStrictEqual(closed.pts, ringAt(L));
  assert.strictEqual(runCoreOnOutline(coreExe, sceneDir, "coord_at_out", closed.pts).accepted, true);

  /* 超界一單位:從乾淨草稿落點（草稿裡不能已經有 x=L 的頂點，否則 ±8mm 頂點吸附會把
     L+1 吸回 L —— 見本測試最後一段，那是預期行為不是漏洞）。 */
  const overPlace = PD.place(PD.place(PD.createState(), [0, 0], o).state, [L + 1, 0], o);
  assert.strictEqual(overPlace.error && overPlace.error.code, "OUT_OF_RANGE",
    "超出核心實測邊界一單位就必須擋下：" + JSON.stringify(overPlace.error));
  const atPlace = PD.place(PD.place(PD.createState(), [0, 0], o).state, [L, 0], o);
  assert.strictEqual(atPlace.error, null, "恰為邊界要放行（與核心同一條線）");

  let sNeg = PD.createState();
  const negRing = [[-L, 0], [0, 0], [0, 500], [-L, 500]];
  for (const p of negRing) {
    const r = PD.place(sNeg, p, o);
    assert.strictEqual(r.error, null, "恰為下限的座標必須放行：" + JSON.stringify(p));
    sNeg = r.state;
  }
  const overNeg = PD.place(PD.place(PD.createState(), [0, 0], o).state, [-L - 1, 0], o);
  assert.strictEqual(overNeg.error && overNeg.error.code, "OUT_OF_RANGE");

  /* 吸附在驗證之前跑（§1 的既有管線順序）:落在既有頂點 ±8mm/zoom 內的超界點會先被
     吸附回那個合法頂點，才輪到範圍檢查——所以它不會 OUT_OF_RANGE，而是照吸附後的點
     判定。這是預期行為（真正送出去的是吸附後的座標），在此釘住，免得下一輪複審把它
     當成漏洞：這裡 (L+1,500) 被吸回既有頂點 (L,500)，於是變成沿末段回頭。 */
  const snapped = PD.place(s, [L + 1, 500], o);
  assert.strictEqual(snapped.error && snapped.error.code, "BACKTRACK",
    "超界一單位但落在既有頂點吸附範圍內 → 先吸附回 (L,500)，再依吸附後的點判定");

  console.log(`[跨層裁判 GEO-180] 座標邊界實測:±${L} → ACCEPT、±${L + 1} → REJECT` +
    `（core.exe 訊息「座標或尺寸超出支援範圍」；current_geometry.c:43-47 兩端含等號、:239 逐點檢查）`);

  fs.rmSync(sceneDir, { recursive: true, force: true });
});
