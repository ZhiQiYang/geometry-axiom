#!/usr/bin/env python3
"""下角材幾何 oracle(平釘天花,第一版)。

用途:把「依物理目標推出的下角材幾何」寫成可執行、可檢查的唯一參考。
任何實作(核心、模板、介面、其他 AI)產生的角材幾何,都以本程式的 JSON 輸出逐支比對;
文字說明只是註解,以程式為準。

物理目標(使用者 2026-10-15 講明,見決策佇列補登第 16 項):
  G1 面材每條邊都有支撐:牆邊、柱邊、板縫都要落在角材上,且每側承接寬度 >= X。
  G2 副支(含板端縫上的副支)中心距不超過上限 M;各格盡量一致(同一治具),餘數放最後一格。
  G3 主支整支連續,端到端把力傳到 RC。主支線若穿過 RC 後又回到室內(柱、凸出),
     主支勢必被切斷,屬排板衝突,改用其他起鋪角或板長方向。
  G4 RC 邊界一律有角材(側面固定在 RC 上)。其他角材的端面只頂角材,不頂 RC。
     與主支平行的柱面,其角材沿線延伸到兩端的牆,成為連續的支,讓兩側的副支都有角材可頂。
     與主支平行的外牆在凹角處(牆線越過牆端仍是室內:L 形內角、壁柱、壁龕)停在牆端,
     改由凹角另一面的邊界材越過凹角延伸,停在最近的主支側面,沿牆料的端面頂在這段延伸上。
     這是核心 I22 / R19(e) 唯一接受的表示法(2026-10-16 P-145,原生探針 p1–p9):
     非 boundary 角材不得超出它貼的外牆;延伸段側面以優先級 2 計,主支不得頂它,
     所以頂在延伸段上的沿牆料核心角色是 custom、優先級 3;主支端面落在延伸段上的排法判衝突。
  G5 角材之間、角材與 RC 之間不得有正面積重疊(碰撞);端面相貼是零面積,允許。
  G6 封板從起鋪角整片鋪,只在對牆收邊,不置中。
  G7 最後一條縫若讓縫上的角材撞到對牆的角材(距離 d > D - 1.5w),
     把該縫往內挪到 floor(D - 1.5w),留一條收邊板。第一條縫也適用同一規則。
不處理:樑高度、交丁、角材怎麼固定(與幾何無關)。

座標:世界座標,整數 mm。A 軸 = 板寬方向(主支之間的方向),B 軸 = 板長方向(主支的長度方向)。
奇數寬角材的足跡:中心 c 取 [c - floor(w/2), c + ceil(w/2)],多出的 1 mm 在 + 側。
"""
import json
import math
import sys

# ---------------------------------------------------------------- 區間
def iv_norm(ivs):
    out = []
    for a, b in sorted((a, b) for a, b in ivs if b > a):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def iv_intersect(x, y):
    out, i, j = [], 0, 0
    while i < len(x) and j < len(y):
        a, b = max(x[i][0], y[j][0]), min(x[i][1], y[j][1])
        if b > a:
            out.append((a, b))
        if x[i][1] < y[j][1]:
            i += 1
        else:
            j += 1
    return out


def iv_subtract(x, y):
    out = []
    y = iv_norm(y)
    for a, b in x:
        cur = a
        for c, d in y:
            if d <= cur or c >= b:
                continue
            if c > cur:
                out.append((cur, c))
            cur = max(cur, d)
            if cur >= b:
                break
        if cur < b:
            out.append((cur, b))
    return out


def iv_find(ivs, v):
    for a, b in ivs:
        if a < v < b:
            return (a, b)
    return None


# ---------------------------------------------------------------- 矩形 (x0, y0, x1, y1)
def rng(r, k):
    return (r[k], r[k + 2])


def mk(a, ar, br):
    """依軸 a(0=x,1=y)組矩形:ar 是 A 軸區間,br 是 B 軸區間。"""
    return (ar[0], br[0], ar[1], br[1]) if a == 0 else (br[0], ar[0], br[1], ar[1])


def overlap(r, s):
    return max(r[0], s[0]) < min(r[2], s[2]) and max(r[1], s[1]) < min(r[3], s[3])


def rect_sub(r, s):
    if not overlap(r, s):
        return [r]
    out = []
    x0, y0, x1, y1 = r
    if s[1] > y0:
        out.append((x0, y0, x1, s[1]))
    if s[3] < y1:
        out.append((x0, s[3], x1, y1))
    my0, my1 = max(y0, s[1]), min(y1, s[3])
    if s[0] > x0:
        out.append((x0, my0, s[0], my1))
    if s[2] < x1:
        out.append((s[2], my0, x1, my1))
    return [q for q in out if q[2] > q[0] and q[3] > q[1]]


def leftover(r, rects):
    rest = [r]
    for s in rects:
        nxt = []
        for q in rest:
            nxt.extend(rect_sub(q, s))
        rest = nxt
        if not rest:
            break
    return rest


# ---------------------------------------------------------------- 區域(外環減孔,正交多邊形)
class Region:
    def __init__(self, outer, holes):
        self.rings = [[tuple(p) for p in outer]] + [[tuple(p) for p in h] for h in holes]
        pts = [p for ring in self.rings for p in ring]
        self.coords = [sorted({p[0] for p in pts}), sorted({p[1] for p in pts})]
        o = self.rings[0]
        self.bbox = (min(p[0] for p in o), min(p[1] for p in o), max(p[0] for p in o), max(p[1] for p in o))
        for ring in self.rings:
            for i in range(len(ring)):
                p, q = ring[i], ring[(i + 1) % len(ring)]
                assert p[0] == q[0] or p[1] == q[1], f"非正交邊 {p}->{q}"

    @staticmethod
    def _ring_section(ring, k, m):
        o = 1 - k
        vals = sorted(p[o] for i, p in enumerate(ring)
                      for q in [ring[(i + 1) % len(ring)]]
                      if p[o] == q[o] and min(p[k], q[k]) < m < max(p[k], q[k]))
        assert len(vals) % 2 == 0
        return [(vals[i], vals[i + 1]) for i in range(0, len(vals), 2)]

    def section(self, k, m):
        """在軸 k 座標 m 處,沿另一軸的室內區間。"""
        inner = self._ring_section(self.rings[0], k, m)
        holes = [iv for h in self.rings[1:] for iv in self._ring_section(h, k, m)]
        return iv_subtract(inner, holes)

    def strip_set(self, k, lo, hi):
        """軸 k 上 [lo,hi] 的整條帶子,沿另一軸完全在室內的區間。"""
        cs = self.coords[k]
        if lo < cs[0] or hi > cs[-1] or hi <= lo:
            return []
        bounds = sorted({lo, hi} | {c for c in cs if lo < c < hi})
        res = None
        for p, q in zip(bounds, bounds[1:]):
            s = self.section(k, (p + q) / 2)
            res = s if res is None else iv_intersect(res, s)
            if not res:
                return []
        return res

    def inside(self, x, y):
        return iv_find(self.section(0, x), y) is not None

    def rects(self):
        xs = self.coords[0]
        return [(xa, y0, xb, y1) for xa, xb in zip(xs, xs[1:]) for y0, y1 in self.section(0, (xa + xb) / 2)]

    def edges(self):
        for ring in self.rings:
            for i in range(len(ring)):
                yield ring[i], ring[(i + 1) % len(ring)]

    def outer_edges(self):
        o = self.rings[0]
        return [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]


# ---------------------------------------------------------------- 縫
def seam_centers(lo, hi, start, ps, g, w, mut):
    """從起鋪側整片鋪,回傳縫中心(世界座標)。G6、G7。"""
    T, D = ps + g, hi - lo
    ds = []
    i = 0
    while (i + 1) * T < D:
        ds.append(i * T + ps + g // 2)
        i += 1
    moved = None
    if ds and "no_sliver" not in mut and ds[-1] > D - 1.5 * w:
        new = math.floor(D - 1.5 * w)
        moved = (ds[-1], new)
        ds[-1] = new
    out = [lo + d if start == "min" else hi - d for d in ds]
    return out, moved


# ---------------------------------------------------------------- 建構
def build(room, layout, p, mut=frozenset()):
    P, Lp, g, w, M = p["P"], p["L"], p["gap"], p["w"], p["M"]
    assert g % 2 == 0, "第一版只處理偶數縫寬"
    reg = Region(room["outer"], room.get("holes", []))
    a = 0 if layout["A"] == "x" else 1
    b = 1 - a
    lo_h, hi_h = w // 2, w - w // 2
    Amin, Amax = reg.bbox[a], reg.bbox[a + 2]
    Bmin, Bmax = reg.bbox[b], reg.bbox[b + 2]
    conflicts, timbers = [], []

    def add(kind, rect, **meta):
        timbers.append(dict(id=len(timbers), kind=kind, rect=rect, **meta))
        return timbers[-1]

    def pt(av, bv):
        return (av, bv) if a == 0 else (bv, av)

    # 縫(G6、G7)
    shift = 20 if "shift_origin" in mut else 0  # 突變:起鋪點整組錯移 20 mm,其餘幾何照樣自洽
    seams_a, moved_a = seam_centers(Amin + shift, Amax + shift, layout["a_start"], P, g, w, mut)
    seams_b, moved_b = seam_centers(Bmin, Bmax, layout["b_start"], Lp, g, w, mut)
    # RC 邊界角材(G4)
    astrips, bedges = [], []
    outer = set(reg.outer_edges())
    for e0, e1 in reg.edges():
        if e0[b] == e1[b]:  # 與 A 軸平行:邊界材
            e = e0[b]
            s0, s1 = sorted((e0[a], e1[a]))
            plus = reg.inside(*pt((s0 + s1) / 2, e + 0.5))
            br = (e, e + w) if plus else (e - w, e)
            if "no_column_strips" in mut and room.get("holes") and any(
                    (e0 in h and e1 in h) for h in [[tuple(q) for q in hh] for hh in room["holes"]]):
                continue
            astrips.append(add("boundary", mk(a, (s0, s1), br), rc_line=e, edge=(s0, s1), outer=(e0, e1) in outer))
        else:
            e = e0[a]
            s0, s1 = sorted((e0[b], e1[b]))
            plus = reg.inside(*pt(e + 0.5, (s0 + s1) / 2))
            if "no_column_strips" in mut and room.get("holes") and any(
                    (e0 in h and e1 in h) for h in [[tuple(q) for q in hh] for hh in room["holes"]]):
                continue
            bedges.append((e, (s0, s1), plus, (e0, e1) in outer))
    # 主支:每條 A 向縫一支,整支連續(G3)。先於沿牆料算出,凹角處的邊界材延伸要停在它們側面。
    mains = []
    for c in seams_a:
        ar = (c - lo_h, c + hi_h)
        line = reg.strip_set(a, c, c + 1)
        if not line:
            continue
        if len(line) > 1 and "allow_split" not in mut:
            conflicts.append(dict(code="MAIN_LINE_CROSSES_RC", seam=c, pieces=line))
            continue
        blocks = [rng(s["rect"], b) for s in astrips if max(ar[0], rng(s["rect"], a)[0]) < min(ar[1], rng(s["rect"], a)[1])]
        comps = iv_subtract(line, blocks)
        if len(comps) != 1 and "allow_split" not in mut:
            conflicts.append(dict(code="MAIN_BLOCKED_BY_RC_TIMBER", seam=c, pieces=comps))
            continue
        for comp in comps:
            mains.append(add("main", mk(a, ar, comp), seam=c))
    if "shift_main" in mut:
        for t in mains:
            r = t["rect"]
            t["rect"] = (r[0] + 15, r[1], r[2] + 15, r[3]) if a == 0 else (r[0], r[1] + 15, r[2], r[3] + 15)
    # 與主支平行的 RC 面(G4)。
    # 牆與柱:沿線延伸,直到頂到邊界材或牆,讓兩側的副支都有角材可頂。
    # 外牆在凹角(該牆線越過牆端仍是室內)處停在牆端:核心 I22 不准非 boundary 角材超出它貼的那條外牆,
    # 所以改由凹角另一面的邊界材越過凹角延伸,停在最近的主支側面(R19(e)),沿牆料的端面頂在這段延伸上。
    # 頂在延伸段上的沿牆料,核心角色要用 custom、優先級 3(I22:延伸段側面以優先級 2 計,主支不得頂它)。
    bprims = []
    seen = set()
    reflex = []
    for e, (s0, s1), plus, is_outer in bedges:
        ar = (e, e + w) if plus else (e - w, e)
        line = reg.strip_set(a, *ar)
        iv = iv_find(line, (s0 + s1) / 2)
        if iv is None:
            conflicts.append(dict(code="RC_FACE_STRIP_OUTSIDE", at=[e, s0, s1]))
            continue
        blocks = [rng(s["rect"], b) for s in astrips if max(ar[0], rng(s["rect"], a)[0]) < min(ar[1], rng(s["rect"], a)[1])]
        comp = iv_find(iv_subtract([iv], blocks), (s0 + s1) / 2)
        if comp is None:
            conflicts.append(dict(code="RC_FACE_STRIP_BLOCKED", at=[e, s0, s1]))
            continue
        ends = []
        if is_outer and "rc_through_reflex" not in mut:
            if comp[0] < s0:
                ends.append(s0)
            if comp[1] > s1:
                ends.append(s1)
            comp = (max(comp[0], s0), min(comp[1], s1))
        r = mk(a, ar, comp)
        if r in seen:
            continue
        seen.add(r)
        t = add("rc_parallel", r, rc_line=e)
        if ends:
            t["core_role"] = "custom"
            reflex.extend((e, s) for s in ends)
        bprims.append(t)
    for e, s in ([] if "no_boundary_extension" in mut else reflex):
        for t in astrips:
            if not t["outer"] or t["rc_line"] != s or e not in t["edge"]:
                continue
            lo, hi = rng(t["rect"], a)
            br = rng(t["rect"], b)
            d = -1 if t["edge"][0] == e else 1  # 往遠離自己那條牆的方向越過凹角
            comp = iv_find(reg.strip_set(b, *br), e + d * 0.5)
            if comp is None:
                conflicts.append(dict(code="REFLEX_EXTENSION_OUTSIDE", at=[e, s]))
                continue
            stop = comp[0] if d < 0 else comp[1]
            for q in mains + bprims:
                qa, qb = rng(q["rect"], a), rng(q["rect"], b)
                if max(qb[0], br[0]) >= min(qb[1], br[1]):
                    continue
                if d < 0 and qa[1] <= e:
                    stop = max(stop, qa[1])
                if d > 0 and qa[0] >= e:
                    stop = min(stop, qa[0])
            t["rect"] = mk(a, (stop, hi) if d < 0 else (lo, stop), br)
            t["ext"] = t.get("ext", []) + [[min(e, stop), max(e, stop)]]
    # 主支端面落在凹角延伸段上:核心 I22 把延伸段側面當優先級 2,主支不得頂它 → 這個起鋪角/方向不能用
    ext_rects = [mk(a, tuple(x), rng(t["rect"], b)) for t in astrips for x in t.get("ext", [])]
    for t in mains:
        lo, hi = rng(t["rect"], b)
        o = rng(t["rect"], a)
        for e0, e1 in ((lo - 1, lo), (hi, hi + 1)):
            slab = mk(a, o, (e0, e1))
            if any(overlap(slab, x) for x in ext_rects):
                conflicts.append(dict(code="MAIN_END_ON_REFLEX_EXTENSION", id=t["id"], end=e1 if e0 == lo - 1 else e0))
    # 副支:逐跨、逐格(G2)
    prims = mains + bprims
    crit = sorted({v for t in prims + astrips for v in rng(t["rect"], b)} | set(reg.coords[b]))
    bands = {}
    for b0, b1 in zip(crit, crit[1:]):
        bm = (b0 + b1) / 2
        act = sorted((t for t in prims if rng(t["rect"], b)[0] < bm < rng(t["rect"], b)[1]),
                     key=lambda t: rng(t["rect"], a)[0])
        sec = reg.section(b, bm)
        ast = [s for s in astrips if rng(s["rect"], b)[0] < bm < rng(s["rect"], b)[1]]
        for t, u in zip(act, act[1:]):
            g0, g1 = rng(t["rect"], a)[1], rng(u["rect"], a)[0]
            if g1 <= g0:
                continue
            inside = iv_intersect(sec, [(g0, g1)])
            if not inside:
                continue
            if inside != [(g0, g1)]:
                conflicts.append(dict(code="SPAN_PARTLY_RC", between=[t["id"], u["id"]], at=bm))
                continue
            cover = [s for s in ast if max(g0, rng(s["rect"], a)[0]) < min(g1, rng(s["rect"], a)[1])]
            if cover:
                if any(rng(s["rect"], a)[0] <= g0 and rng(s["rect"], a)[1] >= g1 for s in cover):
                    continue
                conflicts.append(dict(code="SPAN_PARTLY_BLOCKED", between=[t["id"], u["id"]], at=bm))
                continue
            bands.setdefault((t["id"], u["id"]), []).append((b0, b1))
    spans = []
    for key, bl in bands.items():
        for sb0, sb1 in iv_norm(bl):
            spans.append((key, sb0, sb1))
    marks_out = []
    for (tid, uid), sb0, sb1 in sorted(spans, key=lambda s: (s[1], s[0])):
        g0, g1 = rng(timbers[tid]["rect"], a)[1], rng(timbers[uid]["rect"], a)[0]
        lines = []
        for edge, want in ((sb0, 1), (sb1, 0)):
            hit = [s for s in astrips if rng(s["rect"], b)[want] == edge
                   and rng(s["rect"], a)[0] <= g0 and rng(s["rect"], a)[1] >= g1]
            if not hit:
                conflicts.append(dict(code="SPAN_END_NOT_ON_BOUNDARY", between=[tid, uid], at=edge))
                lines.append(None)
            else:
                lines.append(hit[0]["rc_line"])
        if None in lines:
            continue
        # 記號從端部角材的「牆線」起算:角材佔 [線, 線+w]。一般牆邊就是 rc_line;
        # 凹角延伸段在格子外側,改由它朝格子的那一面回推一個料寬,間距上限才算得對。
        line0, line1 = sb0 - w, sb1 + w
        inner = sorted(e for e in seams_b if sb0 < e < sb1)
        bounds = [(line0, "rc")] + [(e, "seam") for e in inner] + [(line1, "rc")]
        start_low = layout["b_start"] == "min"
        span_marks = []
        for (c0, k0), (c1, k1) in zip(bounds, bounds[1:]):
            L = c1 - c0
            if k0 == "seam" and k1 == "seam":
                anchor, d = (c0, 1) if start_low else (c1, -1)
            elif k0 == "seam":
                anchor, d = c0, 1
            elif k1 == "seam":
                anchor, d = c1, -1
            else:
                anchor, d = (c0, 1) if start_low else (c1, -1)
            n = math.floor(L / M) if "floor_n" in mut else math.ceil(L / M)
            n = max(n, 1)
            m = math.ceil(L / n)
            ms = [anchor + d * m * j for j in range(1, n)]
            span_marks.append(dict(cell=[c0, c1], L=L, n=n, m=m, anchor=anchor, marks=sorted(ms)))
            for c in ms:
                if "drop_mark" in mut and c == ms[0]:
                    continue
                add("secondary", mk(a, (g0, g1), (c - lo_h, c + hi_h)), at=c, role="mark", span=[tid, uid])
        for e in inner:
            add("secondary", mk(a, (g0, g1), (e - lo_h, e + hi_h)), at=e, role="seam", span=[tid, uid])
        marks_out.append(dict(span=[tid, uid], b_range=[sb0, sb1], cells=span_marks))
    # 碰撞與入 RC 都是排板衝突(G5):這個起鋪角/方向不能用
    if "skip_conflict_scan" not in mut:
        R = reg.rects()
        for t in timbers:
            if leftover(t["rect"], R):
                conflicts.append(dict(code="TIMBER_INTO_RC", id=t["id"], kind=t["kind"], rect=list(t["rect"])))
        for i in range(len(timbers)):
            for j in range(i + 1, len(timbers)):
                if overlap(timbers[i]["rect"], timbers[j]["rect"]):
                    ks = {timbers[i]["kind"], timbers[j]["kind"]}
                    code = ("MAIN_HITS_RC_TIMBER" if "main" in ks and ks & {"rc_parallel", "boundary"} else
                            "SEAM_TOO_CLOSE_TO_RC" if "secondary" in ks else
                            "TIMBERS_COLLIDE")
                    conflicts.append(dict(code=code, ids=[i, j], kinds=sorted(ks),
                                          rects=[list(timbers[i]["rect"]), list(timbers[j]["rect"])]))
    return dict(region=reg, a=a, b=b, layout=dict(layout), seams_a=seams_a, seams_b=seams_b, moved_a=moved_a, moved_b=moved_b,
                timbers=timbers, conflicts=conflicts, spans=marks_out)


# ---------------------------------------------------------------- 檢查用的獨立縫位推算(不呼叫 seam_centers)
def expected_seam_positions(lo, hi, start, panel, gap, width):
    """G6/G7 另寫一次:從起鋪側量起,第 k 條縫中心距起鋪牆 k·(panel+gap)+panel+gap/2,
    只要下一片板的起點仍在對牆之內就有這條縫;最後一條縫距起鋪牆超過 D-1.5w 時挪到 floor(D-1.5w)。"""
    span = hi - lo
    dist = []
    k = 0
    while (k + 1) * (panel + gap) < span:
        dist.append(k * (panel + gap) + panel + gap // 2)
        k += 1
    if dist and dist[-1] * 2 > 2 * span - 3 * width:  # 整數比較:d > D - 1.5w
        dist[-1] = (2 * span - 3 * width) // 2
    return [lo + d for d in dist] if start == "min" else [hi - d for d in dist]


# ---------------------------------------------------------------- 檢查(與建構分開,用來抓錯)
def check(res, p):
    reg, a, b = res["region"], res["a"], res["b"]
    w, M, X, g = p["w"], p["M"], p["X"], p["gap"]
    T = [t["rect"] for t in res["timbers"]]
    fails = []
    # C7 縫位必須等於獨立推算的起鋪結果(G6/G7)。之後的 C3/C4/C5 也改用這組獨立縫位,
    # 不拿建構輸出當「期望」,所以整組錯移但彼此自洽的幾何會在這裡被抓到。
    lay = res["layout"]
    exp_a = expected_seam_positions(reg.bbox[a], reg.bbox[a + 2], lay["a_start"], p["P"], g, w)
    exp_b = expected_seam_positions(reg.bbox[b], reg.bbox[b + 2], lay["b_start"], p["L"], g, w)
    if sorted(exp_a) != sorted(res["seams_a"]):
        fails.append(dict(check="C7_SEAMS_NOT_FROM_START", axis="A", expected=sorted(exp_a), got=sorted(res["seams_a"])))
    if sorted(exp_b) != sorted(res["seams_b"]):
        fails.append(dict(check="C7_SEAMS_NOT_FROM_START", axis="B", expected=sorted(exp_b), got=sorted(res["seams_b"])))
    # C1 不碰撞
    for i in range(len(T)):
        for j in range(i + 1, len(T)):
            if overlap(T[i], T[j]):
                fails.append(dict(check="C1_OVERLAP", ids=[i, j]))
    # C2 不入 RC
    R = reg.rects()
    for t in res["timbers"]:
        if leftover(t["rect"], R):
            fails.append(dict(check="C2_INTO_RC", id=t["id"]))
    # 面材格子
    Amin, Amax, Bmin, Bmax = reg.bbox[a], reg.bbox[a + 2], reg.bbox[b], reg.bbox[b + 2]

    def cuts(lo, hi, seams):
        out, cur = [], lo
        for c in sorted(seams):
            out.append((cur, c - g // 2))
            cur = c + g // 2
        out.append((cur, hi))
        return out

    pieces = []
    for ar in cuts(Amin, Amax, exp_a):  # 面材格子用獨立推算的縫位
        for br in cuts(Bmin, Bmax, exp_b):
            cell = mk(a, ar, br)
            for r in R:
                q = (max(cell[0], r[0]), max(cell[1], r[1]), min(cell[2], r[2]), min(cell[3], r[3]))
                if q[2] > q[0] and q[3] > q[1]:
                    pieces.append((cell, q))
    by_cell = {}
    for cell, q in pieces:
        by_cell.setdefault(cell, []).append(q)
    # C3 每條面材邊都有支撐,承接寬度 >= X
    for cell, qs in by_cell.items():
        for q in qs:
            x0, y0, x1, y1 = q
            sides = [((x0 - 1, y0, x0, y1), lambda s: (x0, s[1], min(x0 + X, x1), s[3])),
                     ((x1, y0, x1 + 1, y1), lambda s: (max(x1 - X, x0), s[1], x1, s[3])),
                     ((x0, y0 - 1, x1, y0), lambda s: (s[0], y0, s[2], min(y0 + X, y1))),
                     ((x0, y1, x1, y1 + 1), lambda s: (s[0], max(y1 - X, y0), s[2], y1))]
            for strip, band in sides:
                for seg in leftover(strip, qs):
                    rest = leftover(band(seg), T)
                    if rest:
                        fails.append(dict(check="C3_EDGE_UNSUPPORTED", band=list(band(seg)), gap=list(rest[0])))
    # C4 副支間距:沿 B 軸,角材之間的空檔 <= M - w
    for cell, qs in by_cell.items():
        for q in qs:
            ar, br = rng(q, a), rng(q, b)
            edges = sorted({ar[0], ar[1]} | {v for t in T for v in rng(t, a) if ar[0] < v < ar[1]})
            for u0, u1 in zip(edges, edges[1:]):
                um = (u0 + u1) / 2
                if any(rng(t, a)[0] < um < rng(t, a)[1] and rng(t, b)[0] <= br[0] and rng(t, b)[1] >= br[1] for t in T):
                    continue  # 這一段被一支 B 向角材整段蓋住
                cov = [rng(t, b) for t in T if rng(t, a)[0] < um < rng(t, a)[1]]
                for f0, f1 in iv_subtract([br], cov):
                    if f1 - f0 > M - w:
                        fails.append(dict(check="C4_SPACING", at=[um, f0, f1], free=f1 - f0))
    # C5 每條縫一支主支(G3)
    for c in exp_a:
        if reg.strip_set(a, c, c + 1):
            n = sum(1 for t in res["timbers"] if t["kind"] == "main" and t.get("seam") == c)
            if n != 1:
                fails.append(dict(check="C5_MAIN_NOT_SINGLE", seam=c, count=n))
    # C6 端面只頂角材(G4)
    for t in res["timbers"]:
        if t["kind"] == "boundary":
            continue
        k = b if t["kind"] in ("main", "rc_parallel") else a
        r = t["rect"]
        lo, hi = rng(r, k)
        o = rng(r, 1 - k)
        for end in ((lo - 1, lo), (hi, hi + 1)):
            slab = (end[0], o[0], end[1], o[1]) if k == 0 else (o[0], end[0], o[1], end[1])
            if leftover(slab, [s for s in T if s != r]):
                fails.append(dict(check="C6_END_NOT_ON_TIMBER", id=t["id"], end=list(end)))
    # C8 核心可表示(只查外牆;孔邊在核心沒有定位邊與延伸段)。與建構分開,直接照核心的規則重算:
    #   定位邊 = 與角材某側面共線、長度區間正重疊的外牆邊;有整條覆蓋者優先,其次重疊最長,同分取先出現者
    #   (current_geometry.c timber_role_props)。
    #   C8a I22:非 boundary 角材的長度區間不得超出定位邊。
    #   C8b I19:boundary 在定位邊端點結束的端面,室內那部分只能頂另一支 boundary(轉角互頂);
    #        超出定位邊的延伸段端面須頂到角材或牆。
    #   C8c I22:延伸段側面以優先級 2 計,主支端面不得頂它。
    oe = reg.outer_edges()

    def pos_edge(rect, k):
        span, side = rng(rect, k), rng(rect, 1 - k)
        best = None
        for p0, p1 in oe:
            if p0[1 - k] != p1[1 - k] or p0[1 - k] not in side:
                continue
            elo, ehi = sorted((p0[k], p1[k]))
            ov = min(span[1], ehi) - max(span[0], elo)
            if ov <= 0:
                continue
            cov = span[0] <= elo and span[1] >= ehi
            if best is None or (cov and not best[2]) or (cov == best[2] and ov > best[3]):
                best = (elo, ehi, cov, ov)
        return best

    def end_slabs(rect, k):
        lo, hi = rng(rect, k)
        o = rng(rect, 1 - k)
        for e0, e1, at in ((lo - 1, lo, lo), (hi, hi + 1, hi)):
            yield at, ((e0, o[0], e1, o[1]) if k == 0 else (o[0], e0, o[1], e1))

    exts = []
    for t in res["timbers"]:
        r = t["rect"]
        if t["kind"] in ("main", "rc_parallel"):
            pe = pos_edge(r, b)
            if pe and not (pe[0] <= rng(r, b)[0] and rng(r, b)[1] <= pe[1]):
                fails.append(dict(check="C8_I22_NON_BOUNDARY_EXTENDS", id=t["id"], span=list(rng(r, b)), edge=list(pe[:2])))
        if t["kind"] != "boundary":
            continue
        pe = pos_edge(r, a)
        if not pe:
            continue
        lo, hi = rng(r, a)
        if lo < pe[0]:
            exts.append(mk(a, (lo, pe[0]), rng(r, b)))
        if hi > pe[1]:
            exts.append(mk(a, (pe[1], hi), rng(r, b)))
        others = [s for s in res["timbers"] if s is not t]
        for at, slab in end_slabs(r, a):
            outdoor = leftover(slab, R)
            indoor = leftover(slab, outdoor)  # 端面外 1 mm 落在室內的部分
            if not indoor:
                continue  # 端面整片頂在牆上
            if (at == lo and lo < pe[0]) or (at == hi and hi > pe[1]):
                if any(leftover(q, [s["rect"] for s in others]) for q in indoor):
                    fails.append(dict(check="C8_EXTENSION_END_FREE", id=t["id"], end=at))
                continue
            bad = [s["id"] for s in others if s["kind"] != "boundary" and any(overlap(q, s["rect"]) for q in indoor)]
            free = any(leftover(q, [s["rect"] for s in others if s["kind"] == "boundary"]) for q in indoor)
            if bad or free:
                fails.append(dict(check="C8_I19_BOUNDARY_END", id=t["id"], end=at, on=bad))
    for t in res["timbers"]:
        if t["kind"] != "main":
            continue
        for at, slab in end_slabs(t["rect"], b):
            if any(overlap(slab, x) for x in exts):
                fails.append(dict(check="C8_MAIN_ON_EXTENSION", id=t["id"], end=at))
    return fails


# ---------------------------------------------------------------- 全部排法
LAYOUTS = [dict(A=A, a_start=sa, b_start=sb) for A in ("x", "y") for sa in ("min", "max") for sb in ("min", "max")]


def layout_name(l):
    long_axis = "Y" if l["A"] == "x" else "X"
    ax = {"x": ("左", "右"), "y": ("上", "下")}
    a_ax, b_ax = l["A"], ("y" if l["A"] == "x" else "x")
    side = {}
    side[a_ax] = ax[a_ax][0] if l["a_start"] == "min" else ax[a_ax][1]
    side[b_ax] = ax[b_ax][0] if l["b_start"] == "min" else ax[b_ax][1]
    return f"{side['x']}{side['y']}起鋪,板長沿{long_axis}"


def solve(room, p, mut=frozenset()):
    out = []
    for l in LAYOUTS:
        res = build(room, l, p, mut)
        fails = check(res, p) if not res["conflicts"] else []
        out.append((l, res, fails))
    return out


def export(room_name, l, res, fails):
    return dict(room=room_name, layout=l, name=layout_name(l),
                seams_a=res["seams_a"], seams_b=res["seams_b"], moved_a=res["moved_a"], moved_b=res["moved_b"],
                conflicts=res["conflicts"], check_failures=fails,
                timbers=[dict(id=t["id"], kind=t["kind"], rect=list(t["rect"]),
                              **{k: v for k, v in t.items() if k in ("seam", "at", "role", "rc_line")})
                         for t in res["timbers"]],
                spans=res["spans"])


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    p = spec["params"]
    allout = []
    for name, room in spec["rooms"].items():
        for l, res, fails in solve(room, p):
            allout.append(export(name, l, res, fails))
    json.dump(allout, sys.stdout, ensure_ascii=False, indent=1)
