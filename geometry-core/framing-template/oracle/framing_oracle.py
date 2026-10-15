#!/usr/bin/env python3
"""下角材幾何 oracle(平釘天花,第一版)。

用途:把「依物理目標推出的下角材幾何」寫成可執行、可檢查的唯一參考。
任何實作(核心、模板、介面、其他 AI)產生的角材幾何,都以本程式的 JSON 輸出逐支比對;
文字說明只是註解,以程式為準。

物理目標(使用者 2026-10-15 講明,見決策佇列補登第 16 項):
  G1 面材每條邊都有支撐:牆邊、柱邊、板縫都要落在角材上,且每側承接寬度 >= X。
  G2 副支中心距不超過上限 M。記號從同一個起點(牆、板端縫)用同一個間距量,所以全室同一組、
     主支兩側自然同一位置;間距一致只是為了用同一治具做記號,差 1–2 mm 無妨(使用者 2026-10-14 第 1 題)。
     板端縫上的副支只要縫兩側板邊各有 >= X 承接,位置可以挪(縫靠近 RC 時貼著 RC 角材放)。
  衝突:只有在上述所有可調整的位置都放不下時才報;報的時候寫明物理原因與數字。
  G3 主支整支連續,端到端把力傳到 RC。主支線碰到壁柱或獨立柱就停在那裡、分成幾段,
     每段兩端都接到 RC(外牆與壁柱停在邊界材側面,獨立柱停在柱面),這仍是連續傳到 RC;
     只有在室內中間斷開去接別的角材才不行(使用者 2026-10-14 第 3 題、2026-10-16)。
     主支位置預設置中在縫上,但只要縫兩側板邊承接 >= X 就可以平移(G1 才是要求)。
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
    half = g // 2 if (start == "min" or "gap_floor_both" in mut) else g - g // 2  # FT01:正向取下界、反向取上界
    ds = []
    i = 0
    while (i + 1) * T < D:
        ds.append(i * T + ps + half)
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
    P, Lp, g, w, M, X = p["P"], p["L"], p["gap"], p["w"], p["M"], p["X"]
    gl, gu = g // 2, g - g // 2  # 縫在世界座標佔 [c-gl, c+gu]:下側板邊 c-gl、上側板邊 c+gu(兩個起鋪方向都一樣)
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

    # 主支:每條 A 向縫一支(G3)。
    # 位置:預設置中在縫上;支撐只要求縫兩側板邊各有 >= X 的承接(G1),所以主支可以平移。
    #   縫太靠近與主支平行的 RC 角材時,主支往外平移到貼著它。平移超過承接容許量時,
    #   靠 RC 那一側的板邊在 RC 角材不在的那幾段承接不足,沿 RC 角材那條線補一段併料(核心 custom、優先級 3)。
    # 碰到 RC:主支線碰到壁柱或獨立柱就停在那裡,分成幾段;每段兩端都接到 RC——外牆與壁柱停在它們的
    #   邊界材側面,獨立柱停在柱面(柱面的角材在主支兩側分段)。這就是「連續傳到 RC」;
    #   只有在室內中間斷開去接別的角材才不行(使用者 2026-10-14 第 3 題、2026-10-16)。
    allow_lo = lo_h - gl - X  # 往 + 平移的上限:- 側板邊承接仍 >= X
    allow_hi = hi_h - gu - X  # 往 - 平移的上限:+ 側板邊承接仍 >= X
    mains, doublings = [], []
    outer_blocks = [s for s in astrips if s["outer"]]
    for c in seams_a:
        ar = (c - lo_h, c + hi_h)
        if not reg.strip_set(a, c, c + 1):
            continue
        push_lo = push_hi = 0  # 需要往 + / 往 - 平移多少
        for q in bprims:
            qa = rng(q["rect"], a)
            if max(qa[0], ar[0]) >= min(qa[1], ar[1]):
                continue
            if not iv_intersect(reg.strip_set(a, c, c + 1), [rng(q["rect"], b)]):
                continue
            if (qa[0] + qa[1]) / 2 < c:
                push_lo = max(push_lo, qa[1] - ar[0])
            else:
                push_hi = max(push_hi, ar[1] - qa[0])
        if "no_main_shift" in mut:
            push_lo = push_hi = 0
        if push_lo and push_hi:
            conflicts.append(dict(code="MAIN_SQUEEZED", seam=c,
                                  why=f"縫 {c} 兩側都有平行的 RC 角材,主支要往兩邊各讓 {push_lo}/{push_hi} mm,放不下"))
            continue
        s = push_lo - push_hi
        ar = (ar[0] + s, ar[1] + s)
        for _ in range(3):
            hit = [q for q in outer_blocks if max(ar[0], rng(q["rect"], a)[0]) < min(ar[1], rng(q["rect"], a)[1])]
            pieces = iv_subtract(reg.strip_set(a, *ar), [rng(q["rect"], b) for q in hit])
            # 主支端面要整片頂在同一支外牆邊界材貼牆的那一段上(核心 R6(d) 恰一個擋面、I22 主支不頂延伸段)
            fix = 0
            for lo_, hi_ in pieces:
                for endv in (lo_, hi_):
                    qs = [q for q in hit if endv in rng(q["rect"], b)]
                    if not qs or any(q["edge"][0] <= ar[0] and ar[1] <= q["edge"][1] for q in qs):
                        continue
                    q = max(qs, key=lambda q: min(ar[1], q["edge"][1]) - max(ar[0], q["edge"][0]))
                    fix = q["edge"][0] - ar[0] if ar[0] < q["edge"][0] else q["edge"][1] - ar[1]
                    break
                if fix:
                    break
            if not fix or "no_end_push" in mut:
                break
            s += fix
            ar = (ar[0] + fix, ar[1] + fix)
        if "split_main_mid" in mut and pieces and c == seams_a[0]:
            lo, hi = pieces[0]
            mid = (lo + hi) // 2
            pieces = [(lo, mid - 50), (mid + 50, hi)] + pieces[1:]
        for comp in pieces:
            mains.append(add("main", mk(a, ar, comp), seam=c, shift=s))
        if s == 0 or (s > 0 and s <= allow_lo) or (s < 0 and -s <= allow_hi):
            continue
        # 承接不足的那一側:板邊帶 [縫 ± g/2, ± X] 中主支蓋不到的部分,沿 RC 角材那條線補併料
        if s < 0:
            need = (ar[1], c + gu + X)
            da = (ar[1], ar[1] + w)
        else:
            need = (c - gl - X, ar[0])
            da = (ar[0] - w, ar[0])
        doublings.append((c, need, da, pieces))
    if "shift_main" in mut:
        for t in mains:
            r = t["rect"]
            t["rect"] = (r[0] + 15, r[1], r[2] + 15, r[3]) if a == 0 else (r[0], r[1] + 15, r[2], r[3] + 15)
    # 柱面(孔邊)上與主支垂直的角材,在主支經過的地方分段:主支停在柱面,柱面角材兩段的端面頂主支側面
    #  (核心 I19:孔邊/柱面優先級 0,任何角色都可頂;柱面料是 secondary,頂 primary 側面合法)。
    for t in [s for s in astrips if not s["outer"]]:
        ta, tb = rng(t["rect"], a), rng(t["rect"], b)
        cuts = [rng(q["rect"], a) for q in mains
                if max(tb[0], rng(q["rect"], b)[0]) < min(tb[1], rng(q["rect"], b)[1])
                and max(ta[0], rng(q["rect"], a)[0]) < min(ta[1], rng(q["rect"], a)[1])]
        if not cuts:
            continue
        parts = iv_subtract([ta], cuts)
        astrips.remove(t)
        t["rect"] = mk(a, parts[0], tb) if parts else None
        if parts:
            astrips.append(t)
        for p_ in parts[1:]:
            astrips.append(add("boundary", mk(a, p_, tb), rc_line=t["rc_line"], edge=t["edge"], outer=False))
    timbers[:] = [t for t in timbers if t["rect"] is not None]
    for i, t in enumerate(timbers):
        t["id"] = i
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
            for q in mains + bprims + [s for s in astrips if s is not t]:
                qa, qb = rng(q["rect"], a), rng(q["rect"], b)
                if max(qb[0], br[0]) >= min(qb[1], br[1]):
                    continue
                if d < 0 and qa[1] <= e:
                    stop = max(stop, qa[1])
                if d > 0 and qa[0] >= e:
                    stop = min(stop, qa[0])
            if stop == e:
                continue
            t["rect"] = mk(a, (stop, hi) if d < 0 else (lo, stop), br)
            t["ext"] = t.get("ext", []) + [[min(e, stop), max(e, stop)]]
    # 併料:在凹角延伸做完之後才放,才會停在延伸段上(核心:custom 可頂延伸段)
    made = []
    for c, need, da, pieces in ([] if "no_doubling" in mut else doublings):
        cover = [rng(q["rect"], b) for q in bprims + astrips
                 if rng(q["rect"], a)[0] <= need[0] and rng(q["rect"], a)[1] >= need[1]]
        for comp in pieces:
            for u0, u1 in iv_subtract([comp], cover):
                iv = iv_find(reg.strip_set(a, *da), (u0 + u1) / 2)
                if iv is None:
                    continue  # 那裡是 RC,沒有板
                stops = [rng(q["rect"], b) for q in bprims + astrips + made
                         if max(da[0], rng(q["rect"], a)[0]) < min(da[1], rng(q["rect"], a)[1])]
                seg = iv_find(iv_subtract([iv], stops), (u0 + u1) / 2)
                if seg is None:
                    conflicts.append(dict(code="MAIN_DOUBLING_BLOCKED", seam=c, at=[u0, u1]))
                    continue
                made.append(add("rc_parallel", mk(a, da, seg), rc_line=da[0], doubling=True, core_role="custom"))
    bprims += made
    # 主支端面落在凹角延伸段上:核心 I22 把延伸段側面當優先級 2,主支不得頂它 → 這個起鋪角/方向不能用
    ext_rects = [mk(a, tuple(x), rng(t["rect"], b)) for t in astrips for x in t.get("ext", [])]
    def end_on_ext(r):
        lo, hi = rng(r, b)
        o = rng(r, a)
        return [x for e0, e1 in ((lo - 1, lo), (hi, hi + 1)) for x in ext_rects if overlap(mk(a, o, (e0, e1)), x)]

    for t in mains:
        hits = end_on_ext(t["rect"])
        if not hits:
            continue
        o = rng(t["rect"], a)
        moved = False
        for x in hits:
            xa = rng(x, a)
            if t.get("shift", 0):
                break  # 已為了避開 RC 角材平移過(可能帶併料),不再動
            for s in ((xa[1] - o[0]) if xa[1] - o[0] <= allow_lo else None,
                      -(o[1] - xa[0]) if o[1] - xa[0] <= allow_hi else None):
                if s is None or s == 0:
                    continue
                r2 = mk(a, (o[0] + s, o[1] + s), rng(t["rect"], b))
                if not end_on_ext(r2) and not leftover(r2, reg.rects()) and not any(
                        overlap(r2, q["rect"]) for q in timbers if q is not t):
                    t["rect"], t["shift"], moved = r2, t.get("shift", 0) + s, True
                    break
            if moved:
                break
        if not moved:
            conflicts.append(dict(code="CORE_LIMIT_MAIN_ON_EXTENSION", id=t["id"],
                                  why="主支端面落在凹角延伸段上;物理上可行,但核心 I22 把延伸段側面當優先級 2,主支不能頂它,平移又超過承接容許量"))
    # 副支(G2)。
    # 記號以整排面材為準:沿 B 軸從牆到牆、以板端縫分格,每格 n=⌈L/M⌉、m=⌈L/n⌉,全室共用同一組記號,
    # 所以主支兩側的副支在同一位置(使用者 2026-10-14 第 1 題:相鄰角材位置要一樣,連接角材才會正交/平行)。
    # 一跨被 RC 角材截斷(凹角、壁柱、柱)時:撞到的記號副支拿掉後間距仍在上限內就拿掉,否則貼著那支角材放。
    # 板端縫上的副支:縫兩側板邊各要 >= X 的承接(G1);縫靠近 RC 角材時副支貼著它放,靠 RC 那側由 RC 角材承接。
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
    # 全室共用的記號(每排面材一組)。先算每一跨的端點與縫上副支,再逐格決定記號:
    # 預設 n=⌈L/M⌉;若某一跨在這一格裡有記號撞到 RC 角材、而拿掉後間距超過上限,就把這一格的 n 加一
    # (整排一起加,記號仍全室對齊),直到每一跨都放得下。
    start_low = layout["b_start"] == "min"

    def gaps(sups, sb0, sb1):
        edges = [sb0] + [v for s in sorted(sups) for v in (s[0], s[1])] + [sb1]
        return [(edges[i], edges[i + 1]) for i in range(0, len(edges), 2)]

    span_rows = []
    for (tid, uid), sb0, sb1 in sorted(spans, key=lambda s: (s[1], s[0])):
        g0, g1 = rng(timbers[tid]["rect"], a)[1], rng(timbers[uid]["rect"], a)[0]
        ok = True
        for edge, want in ((sb0, 1), (sb1, 0)):
            hit = not iv_subtract([(g0, g1)], [rng(s["rect"], a) for s in astrips if rng(s["rect"], b)[want] == edge])
            if not hit:
                conflicts.append(dict(code="SPAN_END_NOT_ON_BOUNDARY", between=[tid, uid], at=edge))
                ok = False
        if not ok:
            continue
        feas = {}
        for e in seams_b:
            need = [(max(x0, sb0), min(x1, sb1)) for x0, x1 in ((e - gl - X, e - gl), (e + gu, e + gu + X))
                    if min(x1, sb1) > max(x0, sb0)]
            if not need:
                continue  # 縫兩側板邊都已在這一跨的端部角材上
            lo_min = max(sb0, max(n1 for n0, n1 in need) - w)
            lo_max = min(sb1 - w, min(n0 for n0, n1 in need))
            if lo_min > lo_max:
                conflicts.append(dict(code="SEAM_SUPPORT_IMPOSSIBLE", between=[tid, uid], seam=e,
                                      why=f"板端縫 {e} 兩側板邊要的承接 {need} 一支 {w} mm 的副支蓋不住"))
                continue
            feas[e] = (lo_min, lo_max)
        span_rows.append(dict(key=(tid, uid), sb0=sb0, sb1=sb1, g0=g0, g1=g1, feas=feas, sups=[]))
    # 縫上副支的位置:同一條縫在主支兩側盡量同一位置(相鄰角材位置一樣);置中只是預設。
    # 各跨可放的範圍有交集就全取同一值(交集內最接近置中者);沒有交集時,取讓相鄰兩跨差距總和最小的共同目標再夾進各跨範圍。
    for e in seams_b:
        rows = [sr for sr in span_rows if e in sr["feas"]]
        if not rows:
            continue
        center = e - lo_h
        if "seam_centered" in mut:
            for sr in rows:
                sr["sups"].append((center, center + w, "seam", e))
            continue
        lo_all = max(sr["feas"][e][0] for sr in rows)
        hi_all = min(sr["feas"][e][1] for sr in rows)
        clamp = lambda v, f: min(max(v, f[0]), f[1])
        if lo_all <= hi_all:
            target = clamp(center, (lo_all, hi_all))
        else:
            pairs = [(x, y) for x in rows for y in rows if x["key"][1] == y["key"][0]]
            cands = sorted({v for sr in rows for v in sr["feas"][e]} | {center})
            target = min(cands, key=lambda v: (sum(abs(clamp(v, x["feas"][e]) - clamp(v, y["feas"][e])) for x, y in pairs), abs(v - center)))
        for sr in rows:
            lo = clamp(target, sr["feas"][e])
            sr["sups"].append((lo, lo + w, "seam", e))

    def fits(sr, c):
        lo, hi = c - lo_h, c + hi_h
        return lo >= sr["sb0"] and hi <= sr["sb1"] and not any(max(lo, s[0]) < min(hi, s[1]) for s in sr["sups"])

    rbounds = [(Bmin, "rc")] + [(e, "seam") for e in sorted(seams_b)] + [(Bmax, "rc")]
    row_marks, row_cells = [], []
    for (c0, k0), (c1, k1) in zip(rbounds, rbounds[1:]):
        L = c1 - c0
        if k0 == "seam" and k1 == "seam":
            anchor, d = (c0, 1) if start_low else (c1, -1)
        elif k0 == "seam":
            anchor, d = c0, 1
        elif k1 == "seam":
            anchor, d = c1, -1
        else:
            anchor, d = (c0, 1) if start_low else (c1, -1)
        n0 = max(1, math.floor(L / M) if "floor_n" in mut else math.ceil(L / M))
        for n in range(n0, n0 + 4):
            m = math.ceil(L / n)
            ms = sorted(anchor + d * m * j for j in range(1, n))
            if "drop_mark" in mut:
                ms = ms[1:]
            bad = False
            for sr in span_rows:
                if sr["sb1"] <= c0 or sr["sb0"] >= c1:
                    continue
                inside = [c for c in ms if sr["sb0"] < c < sr["sb1"]]
                kept = [(c - lo_h, c + hi_h) for c in inside if fits(sr, c)]
                if "fixed_n" in mut or "floor_n" in mut:
                    continue  # 突變:不加密(floor_n 另把格數改成無條件捨去)
                for x0, x1 in gaps(sr["sups"] + kept, sr["sb0"], sr["sb1"]):
                    if x0 >= c0 - w and x1 <= c1 + w and x1 - x0 > M - w:
                        bad = True
            if not bad:
                break
        row_cells.append(dict(cell=[c0, c1], L=L, n=n, m=m, anchor=anchor, marks=ms))
        row_marks += ms

    marks_out = []
    for sr in span_rows:
        sups = list(sr["sups"])
        tid, uid = sr["key"]
        for c in row_marks:
            if sr["sb0"] < c < sr["sb1"] and fits(sr, c):
                off = 20 if ("misalign_marks" in mut and mains and sr["g0"] > rng(mains[0]["rect"], a)[1]) else 0
                sups.append((c - lo_h + off, c + hi_h + off, "mark", c))
        for x0, x1 in gaps(sups, sr["sb0"], sr["sb1"]):
            if x1 - x0 > M - w:
                conflicts.append(dict(code="MARK_NO_ROOM", between=[tid, uid], gap=[x0, x1],
                                      why=f"這一跨 [{x0},{x1}] 的空檔 {x1 - x0} mm 超過 {M - w},記號加密 3 次仍放不下"))
        for lo, hi, role, at in sorted(sups):
            add("secondary", mk(a, (sr["g0"], sr["g1"]), (lo, hi)), at=at, role=role, span=[tid, uid])
        marks_out.append(dict(span=[tid, uid], b_range=[sr["sb0"], sr["sb1"]], supports=[list(s) for s in sorted(sups)]))
    if "one_sided_delete" in mut and mains:
        m0 = rng(mains[0]["rect"], a)
        right = [t_ for t_ in timbers if t_["kind"] == "secondary" and t_.get("role") == "mark" and rng(t_["rect"], a)[0] == m0[1]]
        if right:
            timbers.remove(right[len(right) // 2])
            for i_, t_ in enumerate(timbers):
                t_["id"] = i_
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
    half = gap // 2 if start == "min" else gap - gap // 2  # 提案 FT01:正向 P+⌊gap/2⌋,反向 P+⌈gap/2⌉
    dist = []
    k = 0
    while (k + 1) * (panel + gap) < span:
        dist.append(k * (panel + gap) + panel + half)
        k += 1
    if dist and dist[-1] * 2 > 2 * span - 3 * width:  # 整數比較:d > D - 1.5w
        dist[-1] = (2 * span - 3 * width) // 2
    return [lo + d for d in dist] if start == "min" else [hi - d for d in dist]


def pos_edge_outer(reg, rect, k):
    """與角材某側面共線、長度區間正重疊的外牆邊(沿軸 k)存在嗎。"""
    span, side = rng(rect, k), rng(rect, 1 - k)
    for p0, p1 in reg.outer_edges():
        if p0[1 - k] == p1[1 - k] and p0[1 - k] in side:
            elo, ehi = sorted((p0[k], p1[k]))
            if min(span[1], ehi) - max(span[0], elo) > 0:
                return True
    return False


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
            cur = c + (g - g // 2)
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
    # C5 主支(G3):每條縫的主支段把整條縫線蓋滿(只有 RC 與外牆邊界材處可以斷);
    #    每段兩端都接到 RC:端面外是 RC,或頂在外牆/壁柱的邊界材上。不能在室內中間斷開。
    outer_only = Region(reg.rings[0], [])
    holes_R = [q for r_ in outer_only.rects() for q in leftover(r_, R)]
    ob = [t for t in res["timbers"] if t["kind"] == "boundary" and pos_edge_outer(reg, t["rect"], a)]
    for c in exp_a:
        line = reg.strip_set(a, c, c + 1)
        if not line:
            continue
        ps = [t for t in res["timbers"] if t["kind"] == "main" and t.get("seam") == c]
        cov = [rng(t["rect"], b) for t in ps] + [rng(t["rect"], b) for t in ob + [q for q in res["timbers"] if q["kind"] == "rc_parallel"]
                                                if rng(t["rect"], a)[0] <= c < rng(t["rect"], a)[1]]
        gap = iv_subtract(line, cov)
        if gap:
            fails.append(dict(check="C5_MAIN_GAP", seam=c, gaps=gap))
        for t in ps:
            for at, slab in ((rng(t["rect"], b)[0], mk(a, rng(t["rect"], a), (rng(t["rect"], b)[0] - 1, rng(t["rect"], b)[0]))),
                             (rng(t["rect"], b)[1], mk(a, rng(t["rect"], a), (rng(t["rect"], b)[1], rng(t["rect"], b)[1] + 1)))):
                indoor = leftover(slab, leftover(slab, R))
                if any(leftover(q, [s["rect"] for s in ob]) for q in indoor):
                    fails.append(dict(check="C5_MAIN_END_NOT_ON_RC", id=t["id"], end=at))
    # C6 端面只頂角材(G4);獨立柱面例外:主支停在柱面,柱面角材在主支兩側分段(核心孔邊優先級 0)。
    for t in res["timbers"]:
        if t["kind"] == "boundary":
            continue
        k = b if t["kind"] in ("main", "rc_parallel") else a
        r = t["rect"]
        lo, hi = rng(r, k)
        o = rng(r, 1 - k)
        for end in ((lo - 1, lo), (hi, hi + 1)):
            slab = (end[0], o[0], end[1], o[1]) if k == 0 else (o[0], end[0], o[1], end[1])
            if leftover(slab, [s for s in T if s != r] + holes_R):
                fails.append(dict(check="C6_END_NOT_ON_TIMBER", id=t["id"], end=list(end)))
    # C9 記號對齊:主支一側的記號副支,另一側同一位置若是同樣可以放副支的室內跨,也要有副支在同一位置。
    secs = [t for t in res["timbers"] if t["kind"] == "secondary" and t.get("role") == "mark"]
    for mt in [t for t in res["timbers"] if t["kind"] == "main"]:
        ma, mb = rng(mt["rect"], a), rng(mt["rect"], b)
        left = {rng(s["rect"], b) for s in secs if rng(s["rect"], a)[1] == ma[0] and mb[0] <= rng(s["rect"], b)[0] and rng(s["rect"], b)[1] <= mb[1]}
        right = {rng(s["rect"], b) for s in secs if rng(s["rect"], a)[0] == ma[1] and mb[0] <= rng(s["rect"], b)[0] and rng(s["rect"], b)[1] <= mb[1]}
        for side, mine, other, x0 in (("左", left, right, ma[1]), ("右", right, left, ma[0] - 1)):
            for br in mine - other:
                probe = mk(a, (x0, x0 + 1), br)
                if leftover(probe, R) or any(overlap(probe, s["rect"]) for s in res["timbers"]
                                             if not (s["kind"] == "secondary" and s.get("role") == "mark")):
                    continue  # 另一側那裡是 RC 或別的角材(含縫上副支),那支記號本來就放不下
                fails.append(dict(check="C9_MARKS_NOT_ALIGNED", main=mt["id"], at=list(br), side=side,
                                  other=[list(s) for s in other if max(s[0], br[0] - w) < min(s[1], br[1] + w)]))
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
    for t in res["timbers"]:
        if t["kind"] == "boundary":
            continue
        k = b if t["kind"] in ("main", "rc_parallel") else a
        for at, slab in end_slabs(t["rect"], k):
            indoor = leftover(slab, leftover(slab, R))
            if not indoor:
                continue
            on = [s for s in res["timbers"] if s is not t and any(overlap(q, s["rect"]) for q in indoor)]
            if len(on) != 1 or any(leftover(q, [on[0]["rect"]]) for q in indoor):
                fails.append(dict(check="C8_END_NOT_ON_ONE_TIMBER", id=t["id"], end=at, on=[s["id"] for s in on]))
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
