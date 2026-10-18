#!/usr/bin/env python3
"""下角材幾何 oracle(平釘天花,第一版)。

用途:把「依物理目標推出的下角材幾何」寫成可執行、可檢查的唯一參考。
任何實作(核心、模板、介面、其他 AI)產生的角材幾何,都以本程式的 JSON 輸出逐支比對;
文字說明只是註解,以程式為準。

物理目標(使用者 2026-10-15 講明,見決策佇列補登第 16 項):
  G1 面材每條邊都有支撐:牆邊、柱邊、板縫都要落在角材上,且每側承接寬度 >= X。
  G2 副支中心距不超過上限 M。記號從同一個起點(牆、板端縫)用同一個治具 M 量(使用者 2026-10-18 拍板「乙 同一治具 367」,餘數放最後一段;見 jig_marks),所以全室同一組、
     主支兩側自然同一位置;間距一致是為了用同一治具做記號,現場差 1–2 mm 無妨(轉述;原話見決策佇列第 16 項,台北 10-15 05:51 第 1 題:「間隔差了1~2mm影響不大」)。
     板端縫上的副支只要縫兩側板邊各有 >= X 承接,位置可以挪(縫靠近 RC 時貼著 RC 角材放)。
  衝突:只有在上述所有可調整的位置都放不下時才報;報的時候寫明物理原因與數字。
  G3 主支整支連續,端到端把力傳到 RC。主支線碰到壁柱或獨立柱就停在那裡、分成幾段,
     每段兩端都接到 RC(外牆與壁柱停在邊界材側面,獨立柱停在柱面),這仍是連續傳到 RC;
     只有在室內中間斷開去接別的角材才不行(使用者 台北 10-15 05:51 第 3 題、2026-10-16)。
     主支位置預設置中在縫上,但只要縫兩側板邊承接 >= X 就可以平移(G1 才是要求)。
     R-butt:主支與相鄰平行料之間有 0 < 間隙、平移這段間隙後承接仍 >= X,就平移到貼住,不留 1 mm 縫。
     依據:使用者 台北 10-16 01:29 講的是「副支」位置可以調整(原話:「…這種衝突 可以調整 副支位置 副支的位置我之前說過了 在副支間距上限之下就好…」);
     主支在承接 >= X 內平移、貼住,是 Claude 由同一原則推論出來的,不是使用者原話;
     另依平釘天花工法知識(skill flat-nailed-ceiling,references/edge-rule.md §4「挪縫到主骨剛好 butt 壁邊材」)。
  R-nosliver:副支段長 < min_piece 一律不放,那條窄縫兩側的板由縫兩邊的料承接。
     理由是協調 agent 的物理推論(2026-10-18,不是使用者原話):1–23 mm 的角材現場不存在、釘不上去,
     板跨過那麼窄的縫也不會垂(edge-rule.md §4 也寫收邊格「無副骨,薄板由主骨+壁邊材直接夾持」)。
     min_piece = w = 27 mm 是使用者 2026-10-18 拍板(決策佇列「副支最短長度」,#302);
     RC 柱面上短於 27 mm 的段落也不放邊界材,是同日補拍板(#302 補充),選項原文「不放(短於 27 一律不放)」;
     牆面上的短段比照柱面,是由「一律」推得的推論,不是使用者原話(協調 agent 2026-10-18)。
     檢查 C3/C4/C9 對這種窄縫用 bridged() 判為由兩側承接。
  G4 RC 邊界一律有角材(側面固定在 RC 上)。其他角材的端面只頂角材,不頂 RC。
     與主支平行的柱面,其角材沿線延伸到兩端的牆,成為連續的支,讓兩側的副支都有角材可頂。
     與主支平行的外牆在凹角處(牆線越過牆端仍是室內:L 形內角、壁柱、壁龕)停在牆端,
     改由凹角另一面的邊界材越過凹角延伸,停在路上第一支角材的側面(主支、沿牆料或另一支邊界材;核心 I22 允許延伸段端面頂任何優先級的側面),沿牆料的端面頂在這段延伸上。
     這是核心 I22 / R19(e) 接受的表示法(2026-10-16 P-145,原生探針 p1–p9):
     非 boundary 角材不得超出它貼的外牆;延伸段側面以優先級 2 計,主支不得頂它,
     所以頂在延伸段上的沿牆料核心角色是 custom、優先級 3;主支端面落在延伸段上的排法判衝突。
     I19 另要求端面所頂擋面的優先級嚴格小於自己,副支 3 頂不了 custom 3:端面頂到沿牆料或併料的副支
     改宣告 custom、優先級 4,條文不改(使用者 2026-10-18 拍板,決策佇列「凹角沿牆料的排序」選項 C,#301)。
     檢查 C8_I19_PRIORITY 做這條數值比較。原生核心接受 custom 4:PR #297 在 WSL 實跑 94eae4a3 的 64 個場景,
     接受 2639 支、容量上限拒絕 318 支(沒有走到規則檢查),規則拒絕 0、錯誤 0、幾何不符 0。
  G5 角材之間、角材與 RC 之間不得有正面積重疊(碰撞);端面相貼是零面積,允許。
  G6 封板從起鋪角整片鋪,只在對牆收邊,不置中。
  G7 最後一條縫若讓縫上的角材撞到對牆的角材(距離 d > D - 1.5w),
     把該縫往內挪到 floor(D - 1.5w),留一條收邊板。第一條縫也適用同一規則。
     D 是「縫線上最近的對牆」離起鋪牆的距離(只看外牆;矩形房就是房深)。由平釘工法挪縫目的,
     加上由使用者 台北 10-16 01:29 的原話「…這種衝突 可以調整 副支位置 副支的位置我之前說過了 在副支間距上限之下就好…」推得的原則(推論,不是使用者原話):支撐能調整就調整,找不到調整位置才報衝突:
     挪縫是為了讓主支剛好貼住它實際會碰到的那面牆的壁邊材(edge-rule.md §4 的「房深 − 40.5」);
     有牆階的房間,縫線上實際的對牆不是外框,照外框挪會在可以調整的地方報衝突。挪了縫線變長就重算到穩定。
     最後一條板端縫的承接帶若落進牆階面上沒料的短段(短於 min_piece 不放),再照那面牆階凹角那端的牆退到 ⌊D′ − 1.5w⌋
     (由上面那條推論原則與 G7 推得;退縫之後再照 G7 挪到穩定。建構端在 bedges 之後,C7 用 expected_seam_retreat 另算)。
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
def seam_centers(lo, hi, start, ps, g, w, mut, local=None):
    """從起鋪側整片鋪,回傳縫中心(世界座標)。G6、G7。
    G7 的 D:最後一條縫「縫線上最近的對牆」離起鋪牆多遠(local(d) 給;沒有就用外框深度)。
    由平釘工法挪縫目的(主支剛好貼住它實際會碰到的那面牆的壁邊材,edge-rule.md §4 的「房深 − 40.5」)與
    由使用者 台北 10-16 01:29 的原話「…這種衝突 可以調整 副支位置 副支的位置我之前說過了 在副支間距上限之下就好…」推得的原則(推論,不是使用者原話):支撐能調整就調整,找不到調整位置才報衝突。
    有牆階的房間,縫線上實際的對牆不是外框,照外框挪會在可以調整的地方報衝突。
    挪了之後縫線可能伸進更淺的那一段,所以重算到不再需要挪為止;不會挪過前一條縫。"""
    T, D = ps + g, hi - lo
    half = g // 2 if (start == "min" or "gap_floor_both" in mut) else g - g // 2  # FT01:正向取下界、反向取上界
    ds = []
    i = 0
    while (i + 1) * T < D:
        ds.append(i * T + ps + half)
        i += 1
    moved = None
    if ds and "no_sliver" not in mut:
        for _ in range(8):
            Dl = D if (local is None or "bbox_ft02" in mut) else local(ds[-1])
            if ds[-1] <= Dl - 1.5 * w:
                break
            new = math.floor(Dl - 1.5 * w)
            if len(ds) > 1 and new <= ds[-2]:
                break
            moved = (moved[0] if moved else ds[-1], new)
            ds[-1] = new
    out = [lo + d if start == "min" else hi - d for d in ds]
    return out, moved


def g7_settle(d, d_prev, depth, w):
    """G7 重算到穩定:d > D(d) − 1.5w 就挪到 ⌊D(d) − 1.5w⌋,D 由 depth(d) 給;不挪過前一條縫(d_prev)。整數運算。"""
    for _ in range(8):
        D = depth(d)
        if d * 2 <= 2 * D - 3 * w:
            break
        new = (2 * D - 3 * w) // 2
        if d_prev is not None and new <= d_prev:
            break
        d = new
    return d


def local_depth_fn(reg_outer, k, lo, hi, start):
    """建構用:軸 k 上離起鋪牆 d 的縫線,沿縫線(另一軸)逐段找鋪板方向上第一面外牆,回傳最近那面離起鋪牆的距離。
    只看外環(柱是房間中間的障礙物,由 FT03 主支平移/併料處理,不是收邊的對牆)。"""
    def f(d):
        c = (lo + d - 0.5) if start == "min" else (hi - d + 0.5)  # 往起鋪側偏半 mm:牆剛好在縫上也算在縫前面
        best = None
        for b0, b1 in reg_outer.section(k, c):
            cs = sorted({b0, b1} | {v for v in reg_outer.coords[1 - k] if b0 < v < b1})
            for u0, u1 in zip(cs, cs[1:]):
                iv = iv_find(reg_outer.section(1 - k, (u0 + u1) / 2), c)
                if iv is None:
                    continue
                dd = iv[1] - lo if start == "min" else hi - iv[0]
                best = dd if best is None else min(best, dd)
        return hi - lo if best is None else best
    return f


# ---------------------------------------------------------------- 記號(FT04)
def jig_marks(c0, k0, c1, k1, start_low, M, w, lo_h, hi_h, mut=frozenset()):
    """一格 [c0,c1] 的記號位置。k0/k1 是兩端的種類("seam" 板端縫 / "rc" 牆)。
    使用者 2026-10-18 拍板(決策佇列「2026-10-18 #260 最終文字確認、標題與用詞修正、短格記號治具」第 3 題):「乙 同一治具 367」。
    每條板端縫重新起算(沒有板端縫的那一格從起鋪牆起算),一律用模數 M(同一個治具)畫,餘數留在最後一段,最後一段 <= M。
    餘數太小的處理(協調 agent 推論,不是使用者原話;依使用者台北 10-15 05:51 原話「可能最後一步 會有點誤差 但是在上限以內就完全不影響」):
    最後一支記號的料(置中、寬 w)會碰到格端那支料時——格端是板端縫就是縫上副支(置中、寬 w),也就是餘數 < w;
    格端是牆就是貼牆的邊界材(寬 w)——把最後兩步合併後平分,前一段取上界 ⌈(M + 餘數)/2⌉(沿用 FT04 上界模數的取整慣例)。"""
    L = c1 - c0
    if k0 == "seam" and k1 == "seam":
        anchor, d = (c0, 1) if start_low else (c1, -1)
    elif k0 == "seam":
        anchor, d = c0, 1
    elif k1 == "seam":
        anchor, d = c1, -1
    else:
        anchor, d = (c0, 1) if start_low else (c1, -1)
    n = max(1, math.floor(L / M) if "floor_n" in mut else math.ceil(L / M))
    if "even_split" in mut:  # 突變:退回逐格均分(舊公式 m = ⌈L/n⌉)
        m = math.ceil(L / n)
        return sorted(anchor + d * m * j for j in range(1, n))
    dist = [M * j for j in range(1, n)]
    if dist and "no_merge_split" not in mut:
        r = L - M * (n - 1)
        last = anchor + d * dist[-1]
        end, kind = (c1, k1) if d > 0 else (c0, k0)
        if kind == "seam":
            band = (end, end) if "no_merge_seam_end" in mut else (end - lo_h, end + hi_h)
        else:
            band = (end - w, end) if d > 0 else (end, end + w)
        if min(last + hi_h, band[1]) > max(last - lo_h, band[0]):
            dist[-1] = M * (n - 2) + math.ceil((M + r) / 2)
    return sorted(anchor + d * x for x in dist)


# ---------------------------------------------------------------- 核心角色:副支頂 custom 3 → custom 4
def promote_custom4(timbers, a, b):
    """端面頂到 custom 側面的副支改宣告 custom、優先級 = 擋面 + 1(現行只有 custom 3 → 4)。
    使用者 2026-10-18 拍板(決策佇列「凹角沿牆料的排序」選項 C,#301),條文不改。
    適用對象:核心角色是副支的料——secondary,以及與主支垂直的柱面料(boundary 且不貼外牆;
    這個條件存在,但 golden 與掃描房間目前沒有實例,由 selftest 的合成案例驗)。
    「頂到」:端面座標等於 custom 料的側面座標(A 軸),而且 custom 料在寬向(B 軸)蓋住整個端面。
    只拿原本就是 custom 的料當擋面(先拍快照),升格後的料不再讓別人升格。"""
    customs = [q for q in timbers if q.get("core_role") == "custom"]
    for t in timbers:
        if not (t["kind"] == "secondary" or (t["kind"] == "boundary" and not t["outer"])):
            continue
        lo, hi = rng(t["rect"], a)
        o = rng(t["rect"], b)
        for q in customs:
            qa, qb = rng(q["rect"], a), rng(q["rect"], b)
            if qb[0] <= o[0] and o[1] <= qb[1] and (qa[1] == lo or qa[0] == hi):
                t["core_role"], t["priority"] = "custom", q["priority"] + 1
                break


# ---------------------------------------------------------------- 建構
def build(room, layout, p, mut=frozenset()):
    P, Lp, g, w, M, X = p["P"], p["L"], p["gap"], p["w"], p["M"], p["X"]
    minp = p.get("min_piece", w)  # R-nosliver 的最短料長;= 角材寬,使用者 2026-10-18 拍板 27 mm(決策佇列)
    sliver = 100 if "nosliver_too_wide" in mut else minp  # 突變:門檻誤設成 100,連 93 mm 寬的跨也不放副支

    def too_short(n):
        """R-nosliver:長度 n 的副支段不放?剛好 min_piece 要放(突變 sliver_le 把邊界弄錯成 <=)。"""
        if "allow_short_pieces" in mut:
            return False
        return n <= sliver if "sliver_le" in mut else n < sliver
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
    reg_outer = Region(room["outer"], [])
    seams_a, moved_a = seam_centers(Amin + shift, Amax + shift, layout["a_start"], P, g, w, mut,
                                    local_depth_fn(reg_outer, a, Amin + shift, Amax + shift, layout["a_start"]))
    seams_b, moved_b = seam_centers(Bmin, Bmax, layout["b_start"], Lp, g, w, mut,
                                    local_depth_fn(reg_outer, b, Bmin, Bmax, layout["b_start"]))
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
    # 所以改由凹角另一面的邊界材越過凹角延伸,停在路上第一支角材的側面(I22 允許頂任何優先級;R19(e) 的主支只是一例),沿牆料的端面頂在這段延伸上。
    # 頂在延伸段上的沿牆料,核心角色要用 custom、優先級 3(I22:延伸段側面以優先級 2 計,主支不得頂它)。
    bprims = []
    seen = set()
    reflex = []
    remnants = []  # 牆面上沒被蓋住、短於 min_piece 而不放料的那一小段:(面, 段, 凹角端)
    for e, (s0, s1), plus, is_outer in bedges:
        ar = (e, e + w) if plus else (e - w, e)
        line = reg.strip_set(a, *ar)
        iv = iv_find(line, (s0 + s1) / 2)
        if iv is None:
            conflicts.append(dict(code="RC_FACE_STRIP_OUTSIDE", at=[e, s0, s1]))
            continue
        blocks = [rng(s["rect"], b) for s in astrips if max(ar[0], rng(s["rect"], a)[0]) < min(ar[1], rng(s["rect"], a)[1])]
        free = iv_subtract([iv], blocks)
        comp = iv_find(free, (s0 + s1) / 2)
        if comp is None:
            on_face = [c_ for c_ in free if min(c_[1], s1) > max(c_[0], s0)]
            comp = max(on_face, key=lambda c_: min(c_[1], s1) - max(c_[0], s0)) if on_face else None
        if comp is None and "short_face_conflict" in mut:
            conflicts.append(dict(code="RC_FACE_STRIP_BLOCKED", at=[e, s0, s1]))  # 突變:回到舊行為,短牆面整段被蓋住就報衝突
            continue
        ends = []
        if is_outer and "rc_through_reflex" not in mut:
            if comp is None:  # 這面 RC 整段已被兩端垂直的料蓋住:凹角那一端仍要讓另一面的邊界材越過凹角
                ends = [v for v, beyond in ((s0, iv[0] < s0), (s1, iv[1] > s1)) if beyond]
            else:
                if comp[0] < s0:
                    ends.append(s0)
                if comp[1] > s1:
                    ends.append(s1)
                comp = (max(comp[0], s0), min(comp[1], s1))
        # 短於 min_piece 一律不放。柱面:使用者 2026-10-18 的決定,選項原文「不放(短於 27 一律不放)」(決策佇列 #302 補充);
        #   牆面比照柱面是由「一律」推得的推論,不是使用者原話(協調 agent 2026-10-18):
        #   牆階、短柱面這種 RC 面,沿牆料整段被兩端垂直的料蓋住,或剩下的一段短於 min_piece,就不放料、不報衝突。
        #   這一面的板邊由兩端的料承接(剩下那一小段沿板邊方向跨過);凹角那一端照樣讓另一面的邊界材越過凹角延伸,接住板的轉角。
        if comp is None or (too_short(comp[1] - comp[0]) and "short_face_conflict" not in mut):
            reflex.extend((e, s) for s in ends)
            if comp is not None and is_outer:
                remnants.append(dict(e=e, face=(s0, s1), comp=comp, ends=list(ends)))
            continue
        r = mk(a, ar, comp)
        if r in seen:
            continue
        seen.add(r)
        t = add("rc_parallel", r, rc_line=e)
        if ends:
            t["core_role"], t["priority"] = "custom", 3
            reflex.extend((e, s) for s in ends)
        bprims.append(t)

    # 板端縫落在牆階短段(G7 的延伸;依推論原則:支撐能調整就調整,找不到調整位置才報衝突,見檔頭):最後一條板端縫的承接帶若落進牆面上那段沒料的短段
    #   (短於 min_piece 不放沿牆料),縫上副支在那裡沒有東西可頂,那條板邊就沒有料承接。
    #   往內調整:把那面牆階凹角那一端的牆(淺的那段的牆)當成這條縫的對牆,照 G7 退到 ⌊D' − 1.5w⌋,
    #   D' = 起鋪牆到凹角那端的距離。這是離原位最近、又不違反 G7 的位置:縫線一退到凹角那端之前,
    #   就伸進淺的那段,G7 照那面牆要求 d <= D' − 1.5w(退到只讓承接帶落在延伸段上,淺的那段會剩 8–17 mm 的板條)。
    #   不退過前一條縫;退了還是落在短段裡就維持衝突。退縫之後的副支、記號、碰撞照常由後面的程序判斷。
    def band_hits(cv, cp):
        return [(x0, x1, sd) for x0, x1, sd in ((cv - gl - X, cv - gl, "-"), (cv + gu, cv + gu + X, "+"))
                if min(x1, cp[1]) > max(x0, cp[0])]

    if seams_b and "no_seam_retreat" not in mut:
        start_min = layout["b_start"] == "min"
        for _ in range(4):
            last = seams_b[-1]
            hit = [r_ for r_ in remnants if band_hits(last, r_["comp"])]
            if not hit:
                break
            r_ = hit[0]
            qs = [q for q in r_["ends"] if (q <= r_["comp"][0] if start_min else q >= r_["comp"][1])]
            if not qs:
                break
            q = max(qs) if start_min else min(qs)
            d_new = math.floor((q - Bmin if start_min else Bmax - q) - 1.5 * w)
            c_new = Bmin + d_new if start_min else Bmax - d_new
            prev = seams_b[-2] if len(seams_b) > 1 else None
            inward = c_new < last if start_min else c_new > last
            past_prev = prev is not None and (c_new <= prev if start_min else c_new >= prev)
            if not inward or past_prev:
                break
            # 退縫之後縫線伸進淺的那段,可能又碰到更近的對牆(例:雙牆階),照 G7 再挪到穩定
            if "no_resettle" not in mut:
                dfun = local_depth_fn(reg_outer, b, Bmin, Bmax, layout["b_start"])
                dd = g7_settle(c_new - Bmin if start_min else Bmax - c_new,
                               None if prev is None else (prev - Bmin if start_min else Bmax - prev), dfun, w)
                c_new = Bmin + dd if start_min else Bmax - dd
            moved_b = (moved_b[0] if moved_b else last, c_new)
            seams_b = seams_b[:-1] + [c_new]
    for r_ in remnants:
        for sb in seams_b:
            for x0, x1, sd in band_hits(sb, r_["comp"]):
                cp = r_["comp"]
                conflicts.append(dict(
                    code="SHORT_FACE_SEAM_EDGE_UNSUPPORTED", at=[r_["e"], *r_["face"]], seam=sb,
                    why=f"板端縫 {sb} 的 {sd} 側板邊(承接帶 {x0}–{x1})落在這面 RC({r_['e']},{r_['face'][0]}–{r_['face'][1]})沒被蓋住的那 "
                        f"{cp[1] - cp[0]} mm({cp[0]}–{cp[1]})裡:短於 {minp} 不放沿牆料,縫上副支的端面只能頂 RC,"
                        f"兩旁的料也蓋不到這條板邊;往內退縫也退不開(會退過前一條縫,或凹角那端不在內側)"))

    # 主支:每條 A 向縫一支(G3)。
    # 位置:預設置中在縫上;支撐只要求縫兩側板邊各有 >= X 的承接(G1),所以主支可以平移。
    #   縫太靠近與主支平行的 RC 角材時,主支往外平移到貼著它。平移超過承接容許量時,
    #   靠 RC 那一側的板邊在 RC 角材不在的那幾段承接不足,沿 RC 角材那條線補一段併料(核心 custom、優先級 3)。
    # 碰到 RC:主支線碰到壁柱或獨立柱就停在那裡,分成幾段;每段兩端都接到 RC——外牆與壁柱停在它們的
    #   邊界材側面,獨立柱停在柱面(柱面的角材在主支兩側分段)。這就是「連續傳到 RC」;
    #   只有在室內中間斷開去接別的角材才不行(使用者 台北 10-15 05:51 第 3 題、2026-10-16)。
    if lo_h - gl < X or hi_h - gu < X:
        conflicts.append(dict(code="MAIN_BEARING_IMPOSSIBLE",
                              why=f"一支 {w} mm 的主支置中在 {g} mm 的縫上,兩側承接只有 {lo_h - gl}/{hi_h - gu} mm,不到 {X} mm"))
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

        def collides(ar_):
            """主支放在 ar_ 時,在它實際存在的範圍(整條帶子都在室內的那幾段)會不會撞到與主支平行的 RC 角材。"""
            foot_ = reg.strip_set(a, *ar_)
            return any(max(ar_[0], rng(q["rect"], a)[0]) < min(ar_[1], rng(q["rect"], a)[1])
                       and iv_intersect(foot_, [rng(q["rect"], b)]) for q in bprims)

        # 依推論原則(支撐能調整就調整,找不到調整位置才報衝突,見檔頭):讓開 RC 角材的平移若反而撞到另一支(例:牆階 28–53 mm,縫線在牆階外側那段落在沿牆料上,
        #   但主支在那段本來就在 RC 裡、不存在),而置中的主支在它實際存在的範圍不撞任何料,就不平移。
        if (push_lo or push_hi) and "no_push_fallback" not in mut:
            sh = push_lo - push_hi
            if collides((ar[0] + sh, ar[1] + sh)) and not collides(ar):
                push_lo = push_hi = 0
        if push_lo and push_hi:
            conflicts.append(dict(code="MAIN_SQUEEZED", seam=c,
                                  why=f"縫 {c} 兩側都有平行的 RC 角材,主支要往兩邊各讓 {push_lo}/{push_hi} mm,放不下"))
            continue
        s = push_lo - push_hi
        ar = (ar[0] + s, ar[1] + s)
        # R-butt(推論:使用者 台北 10-16 01:29 說副支位置可以調整;主支在承接 >= X 內平移、貼住是同一原則的推論,加平釘天花工法 edge-rule.md §4):
        #   主支與相鄰平行料之間有 0 < 間隙,而平移這段間隙後縫兩側板邊承接仍 >= X,就把主支平移到貼住那支料,
        #   不留 1–5 mm 的縫。兩側都可貼時貼間隙小的那側(同分貼 - 側)。平移後主支在室內的範圍要不變;做不到就不移。
        if not (push_lo or push_hi) and "no_r_butt" not in mut:
            foot = reg.strip_set(a, *ar)
            near = {}
            for q in bprims:
                qa = rng(q["rect"], a)
                if not iv_intersect(foot, [rng(q["rect"], b)]):
                    continue
                if qa[1] <= ar[0]:
                    near[-1] = min(near.get(-1, ar[0] - qa[1]), ar[0] - qa[1])
                elif qa[0] >= ar[1]:
                    near[1] = min(near.get(1, qa[0] - ar[1]), qa[0] - ar[1])
            if 0 not in near.values():
                opts = sorted((gap_, d) for d, gap_ in near.items() if gap_ <= (allow_hi if d < 0 else allow_lo))
                for gap_, d in opts:
                    ar2 = (ar[0] + d * gap_, ar[1] + d * gap_)
                    if reg.strip_set(a, *ar2) == foot:
                        s, ar = s + d * gap_, ar2
                        break
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
            if collides((ar[0] + fix, ar[1] + fix)) and "no_push_fallback" not in mut:
                break  # 推進牆段會撞到與主支平行的 RC 角材:不推,交給後面的延伸段檢查(物理可行時標核心限制)
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
        # R-nosliver:被主支切剩 < min_piece 的那一段柱面料不放(那段柱面由兩端的沿柱料與主支承接)。
        #   使用者 2026-10-18 補拍板(決策佇列,#302 補充):RC 柱面上短於 27 mm 的段落也不放邊界材。
        parts = [q for q in iv_subtract([ta], cuts) if not too_short(q[1] - q[0])]
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
                # 延伸不出去(凹角另一側緊貼著另一支外牆邊界材,例:牆階 < 27 mm,兩支牆邊料前後錯開、寬向重疊 27−階 mm):
                # 這支邊界材在牆端的端面若有一段落在室內又沒有別的 boundary 可頂,核心 I19 不接受(端面室內部分只能頂另一支
                # boundary),這是核心表示法的限制。這支邊界材本身側面釘牆,端面懸空不影響它承接板邊;旁邊的跨能不能收頭另由
                # SPAN_END_NOT_ON_BOUNDARY 等判斷。
                slab = mk(a, (e - 1, e) if d < 0 else (e, e + 1), br)
                indoor = leftover(slab, leftover(slab, reg.rects()))
                others = [q["rect"] for q in astrips if q is not t]
                free_ = [r_ for q in indoor for r_ in leftover(q, others)]
                if free_ and "no_end_free_flag" not in mut:
                    fb = rng(free_[0], b)
                    conflicts.append(dict(code="CORE_LIMIT_BOUNDARY_END_FREE", id=t["id"], at=[e, s], free=list(fb),
                                          why=f"邊界材 {list(t['rect'])} 在牆端 {e} 的端面有 {fb[1] - fb[0]} mm 落在室內、沒有別的 boundary 可頂;"
                                              f"越過凹角延伸會撞到另一支外牆邊界材(兩支寬向重疊)。核心 I19 只准 boundary 端面的室內部分頂另一支 boundary"))
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
                made.append(add("rc_parallel", mk(a, da, seg), rc_line=da[0], doubling=True, core_role="custom", priority=3))
    bprims += made
    # 主支端面落在凹角延伸段上:核心 I22 把延伸段側面當優先級 2,主支不得頂它 → 這個起鋪角/方向不能用
    ext_rects = [mk(a, tuple(x), rng(t["rect"], b)) for t in astrips for x in t.get("ext", [])]
    def end_on_ext(r):
        lo, hi = rng(r, b)
        o = rng(r, a)
        return [x for e0, e1 in ((lo - 1, lo), (hi, hi + 1)) for x in ext_rects if overlap(mk(a, o, (e0, e1)), x)]

    # 沿牆料、沿柱料(與主支平行、還不是 custom 的 rc_parallel)端面頂到延伸段:核心 I22 把延伸段側面當優先級 2,
    #   primary 2 頂不了它,改宣告 custom、優先級 3,與 P-145 凹角沿牆料、2026-10-18 凹角沿牆料排序的決定同一表示法。
    #   例:20 mm 的牆階,27 mm 寬的沿牆料比牆階寬,端面有 7 mm 落在牆階邊界材越過凹角的延伸段上(#251 審查 60785906)。
    if "no_ext_custom3" not in mut:
        for t in bprims:
            if t.get("core_role") != "custom" and end_on_ext(t["rect"]):
                t["core_role"], t["priority"] = "custom", 3

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
    # 記號以整排面材為準:沿 B 軸從牆到牆、以板端縫分格,每格用同一治具 M 從板端縫量起、餘數留在最後一段(jig_marks),
    # 全室共用同一組記號,所以主支兩側的副支在同一位置(使用者 台北 10-15 05:51 第 1 題:相鄰角材位置要一樣,連接角材才會正交/平行)。
    # 一跨被 RC 角材截斷(凹角、壁柱、柱)時:撞到的記號副支拿掉;拿掉後空檔超過上限,就貼著擋住它的料補一支補位副支(fill)。
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
            if too_short(g1 - g0):
                continue  # R-nosliver:副支會短於 min_piece,不放;這條窄縫兩側的板由縫兩邊的料承接
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
    # 全室共用的記號(每排面材一組),逐格用同一治具 M 畫(jig_marks)。記號撞到擋料或縫上副支就拿掉;
    # 只有擋料(這一跨端點那支不是副支的料)把治具記號撞掉、空檔超過上限時,才貼著那支擋料補一支補位副支(role fill)。
    # 這取代舊的整排加密:加密會改模數,和使用者 2026-10-18 拍板的「乙 同一治具 367」衝突(Claude 推論,不是使用者原話)。
    start_low = layout["b_start"] == "min"

    def gaps(sups, sb0, sb1):
        edges = [sb0] + [v for s in sorted(sups) for v in (s[0], s[1])] + [sb1]
        return [(edges[i], edges[i + 1]) for i in range(0, len(edges), 2)]

    # 治具記號只看格界(使用者 2026-10-18 拍板「乙 同一治具 367」),先算好,縫上副支才能照它定可放範圍。
    rbounds = [(Bmin, "rc")] + [(e, "seam") for e in sorted(seams_b)] + [(Bmax, "rc")]
    row_marks = []
    for (c0, k0), (c1, k1) in zip(rbounds, rbounds[1:]):
        ms = jig_marks(c0, k0, c1, k1, start_low, M, w, lo_h, hi_h, mut)
        if "drop_mark" in mut:
            ms = ms[1:]
        row_marks += ms
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
        ends_forced = set()
        for e in seams_b:
            need = [(max(x0, sb0), min(x1, sb1)) for x0, x1 in ((e - gl - X, e - gl), (e + gu, e + gu + X))
                    if min(x1, sb1) > max(x0, sb0)]
            if not need:
                # 縫兩側板邊都已在這一跨端點的料(柱面料、牆邊料)上。P-180(協調者推論,不是使用者原話):
                #   板邊雖有承接,但少了縫上副支,這一端到下一支治具記號的空檔會超過 M − w,所以縫上副支仍然需要;
                #   它會撞到那支擋料,依使用者台北 10-16 01:29 原話(副支位置可以調整,在副支間距上限之下就好)挪到貼著擋料。
                #   挪過的副支仍垂直於主支,台北 10-15 05:51 原話講的「連接角材正交/平行」這個目的沒有被違反。
                #   這不是補位副支(fill)。例:3600×3000 柱房,柱面料 [1816,1843] 蓋住縫 1831,這一跨的縫上副支放 [1843,1870],
                #   鄰跨在 [1818,1845],兩者差 25 mm。
                if "no_seam_at_end" not in mut:
                    for end, sg in ((sb0, 1), (sb1, -1)):
                        if abs(e - end) >= w:
                            continue
                        fit_ = [c for c in row_marks if sb0 <= c - lo_h and c + hi_h <= sb1 and (c > end if sg > 0 else c < end)]
                        if not fit_:
                            continue
                        c = min(fit_) if sg > 0 else max(fit_)
                        gap_ = (c - lo_h - end) if sg > 0 else (end - (c + hi_h))
                        if gap_ > M - w:
                            lo = end if sg > 0 else end - w
                            feas[e] = (lo, lo)
                            ends_forced.add(e)
                continue
            lo_min = max(sb0, max(n1 for n0, n1 in need) - w)
            lo_max = min(sb1 - w, min(n0 for n0, n1 in need))
            if lo_min > lo_max:
                conflicts.append(dict(code="SEAM_SUPPORT_IMPOSSIBLE", between=[tid, uid], seam=e,
                                      why=f"板端縫 {e} 兩側板邊要的承接 {need} 一支 {w} mm 的副支蓋不住"))
                continue
            feas[e] = (lo_min, lo_max)
        span_rows.append(dict(key=(tid, uid), sb0=sb0, sb1=sb1, g0=g0, g1=g1, feas=feas, sups=[], ends_forced=ends_forced))
    # 縫上副支的可放範圍再加一個條件:與這一跨裡相鄰的治具記號,空檔不超過 M − w。
    #   依使用者台北 10-16 01:29 原話「…這種衝突 可以調整 副支位置 副支的位置我之前說過了 在副支間距上限之下就好…」
    #   推得(推論,不是使用者原話):縫上副支可以挪,但挪了之後與鄰近記號的間距仍要在上限以內;記號照治具不動。
    #   例:F1 右上起鋪板長沿 X,貼內牆那幾跨的縫上副支被逼到 [3146,3173];其他跨若為了對齊跟著挪到 [3151,3178],
    #   與記號 3536 的空檔變 345 mm,超上限。加了這個條件,其他跨的範圍是 [3156,3156](上下各與記號 3536、2802 空 340)。
    #   加上之後沒有可放的位置,就退回原本的範圍(之後由空檔檢查判斷)。
    if "no_seam_window" not in mut:
        for sr in span_rows:
            for e, (f0, f1) in list(sr["feas"].items()):
                if e in sr["ends_forced"]:
                    continue  # 貼擋料的縫上副支位置已定
                inside = [c for c in row_marks if sr["sb0"] < c < sr["sb1"]]
                above = [c for c in inside if c > e]
                below = [c for c in inside if c < e]
                n0, n1 = f0, f1
                if above:
                    n0 = max(n0, min(above) - lo_h - (M - w) - w)
                if below:
                    n1 = min(n1, max(below) + hi_h + (M - w))
                if n0 <= n1:
                    sr["feas"][e] = (n0, n1)
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

    marks_out = []
    for sr in span_rows:
        sups = list(sr["sups"])
        tid, uid = sr["key"]
        dropped = []
        for c in row_marks:
            if sr["sb0"] < c < sr["sb1"] and fits(sr, c):
                off = 20 if ("misalign_marks" in mut and mains and sr["g0"] > rng(mains[0]["rect"], a)[1]) else 0
                sups.append((c - lo_h + off, c + hi_h + off, "mark", c))
            elif sr["sb0"] - w < c < sr["sb1"] + w:
                dropped.append(c)  # 放不下的治具記號(含剛好落在這一跨端點那支擋料上、離端點不到 w 的)
        for _ in range(4):
            big = [(x0, x1) for x0, x1 in gaps(sups, sr["sb0"], sr["sb1"]) if x1 - x0 > M - w]
            if not big or "no_fill" in mut:
                break
            x0, x1 = big[0]
            if x1 - x0 > M:
                break  # 補一支也不夠
            # 撞掉的記號要落在這個空檔附近(w 以內),而且它那一端必須是這一跨的端點(擋住它的邊界材、沿牆料等),
            # 補位副支才貼著那支料放;那一端若是另一支副支,貼上去就成了雙拼,不補,交給下面判 MARK_NO_ROOM。
            cand = []
            for c in dropped:
                if x1 - w < c < x1 + w and x1 == sr["sb1"]:
                    cand.append((abs(c - x1), x1 - w))
                if x0 - w < c < x0 + w and x0 == sr["sb0"]:
                    cand.append((abs(c - x0), x0))
            if "fill_anywhere" in mut and not cand:
                cand = [(0, x1 - w)]
            if not cand:
                break
            lo = min(cand)[1]
            sups.append((lo, lo + w, "fill", lo + lo_h))
        for x0, x1 in gaps(sups, sr["sb0"], sr["sb1"]):
            if x1 - x0 > M - w:
                conflicts.append(dict(code="MARK_NO_ROOM", between=[tid, uid], gap=[x0, x1],
                                      why=f"這一跨 [{x0},{x1}] 的空檔 {x1 - x0} mm 超過 {M - w}:記號照治具不動,"
                                          f"縫上副支在承接與間距的範圍內也挪不開;能補的只有貼著擋住記號的料補一支,這裡也補不上"))
        for lo, hi, role, at in sorted(sups):
            add("secondary", mk(a, (sr["g0"], sr["g1"]), (lo, hi)), at=at, role=role, span=[tid, uid])
        marks_out.append(dict(span=[tid, uid], b_range=[sr["sb0"], sr["sb1"]], supports=[list(s) for s in sorted(sups)]))
    if "drop_mark_row_at_column" in mut and room.get("holes"):
        hb = [(min(q[b] for q in h) + max(q[b] for q in h)) / 2 for h in room["holes"]]
        marks_ = [t_ for t_ in timbers if t_["kind"] == "secondary" and t_.get("role") == "mark"]
        if marks_:
            target = min({t_["at"] for t_ in marks_}, key=lambda v: min(abs(v - c) for c in hb))
            for t_ in [t_ for t_ in marks_ if t_["at"] == target]:
                timbers.remove(t_)
            for i_, t_ in enumerate(timbers):
                t_["id"] = i_
    if "shift_mark_rects" in mut:  # 突變:記號副支的矩形整排移 -8 mm,at 標籤不動
        for t_ in timbers:
            if t_["kind"] == "secondary" and t_.get("role") == "mark":
                t_["rect"] = mk(a, rng(t_["rect"], a), (rng(t_["rect"], b)[0] - 8, rng(t_["rect"], b)[1] - 8))
    if "fill_relabel" in mut:  # 突變:把一支記號移 -8 mm 後改標成 fill
        ms_ = [t_ for t_ in timbers if t_["kind"] == "secondary" and t_.get("role") == "mark"]
        if ms_:
            t_ = ms_[len(ms_) // 2]
            t_["rect"] = mk(a, rng(t_["rect"], a), (rng(t_["rect"], b)[0] - 8, rng(t_["rect"], b)[1] - 8))
            t_["role"] = "fill"
    if "fill_extra" in mut:  # 突變:在兩支記號正中間憑空多放一支 fill
        ms_ = sorted((t_ for t_ in timbers if t_["kind"] == "secondary" and t_.get("role") == "mark"),
                     key=lambda t_: (rng(t_["rect"], a), rng(t_["rect"], b)))
        for t0_, t1_ in zip(ms_, ms_[1:]):
            if rng(t0_["rect"], a) == rng(t1_["rect"], a):
                mid = (rng(t0_["rect"], b)[1] + rng(t1_["rect"], b)[0]) // 2 - w // 2
                add("secondary", mk(a, rng(t0_["rect"], a), (mid, mid + w)), at=mid + lo_h, role="fill", span=t0_["span"])
                break
    for tag_, role_ in (("extra_seam_mid", "seam"), ("extra_norole_mid", None)):
        if tag_ in mut:  # 突變:在兩支記號正中間多放一支,標成 seam 或不給 role
            ms_ = sorted((t_ for t_ in timbers if t_["kind"] == "secondary" and t_.get("role") == "mark"),
                         key=lambda t_: (rng(t_["rect"], a), rng(t_["rect"], b)))
            for t0_, t1_ in zip(ms_, ms_[1:]):
                if rng(t0_["rect"], a) == rng(t1_["rect"], a):
                    mid = (rng(t0_["rect"], b)[1] + rng(t1_["rect"], b)[0]) // 2 - w // 2
                    nt_ = add("secondary", mk(a, rng(t0_["rect"], a), (mid, mid + w)), at=mid + lo_h, span=t0_["span"])
                    if role_:
                        nt_["role"] = role_
                    break
    if "seam_relabel" in mut:  # 突變:把一支記號移 -8 mm 後改標成 seam
        ms_ = [t_ for t_ in timbers if t_["kind"] == "secondary" and t_.get("role") == "mark"]
        if ms_:
            t_ = ms_[len(ms_) // 2]
            t_["rect"] = mk(a, rng(t_["rect"], a), (rng(t_["rect"], b)[0] - 8, rng(t_["rect"], b)[1] - 8))
            t_["role"] = "seam"
    if "fill_double" in mut:  # 突變:把 fill 改成貼著旁邊那支記號(雙拼),不貼擋料
        for t_ in [t_ for t_ in timbers if t_["kind"] == "secondary" and t_.get("role") == "fill"]:
            ta_, tb_ = rng(t_["rect"], a), rng(t_["rect"], b)
            nb = [q for q in timbers if q is not t_ and q["kind"] == "secondary" and rng(q["rect"], a) == ta_ and rng(q["rect"], b)[1] <= tb_[0]]
            if nb:
                top = max(rng(q["rect"], b)[1] for q in nb)
                t_["rect"] = mk(a, ta_, (top, top + w))
                t_["at"] = top + lo_h
                break
    for i_, t_ in enumerate(timbers):
        t_["id"] = i_
    if "one_sided_delete" in mut and mains:
        m0 = rng(mains[0]["rect"], a)
        right = [t_ for t_ in timbers if t_["kind"] == "secondary" and t_.get("role") == "mark" and rng(t_["rect"], a)[0] == m0[1]]
        if right:
            timbers.remove(right[len(right) // 2])
            for i_, t_ in enumerate(timbers):
                t_["id"] = i_
    # 核心角色:端面頂到 custom 側面(凹角沿牆料、併料,custom 優先級 3)的副支,改宣告 custom、優先級 4,條文不改
    #   (使用者 2026-10-18 拍板,決策佇列「凹角沿牆料的排序」選項 C,#301)。I19 要擋面擁有者優先級嚴格小於自己,
    #   副支 3 頂不了 custom 3。依實際擋面判定:端面座標等於那支 custom 料的側面,且它在寬向蓋住整個端面;
    #   只拿原本就是 custom 的料當擋面,升格後的 custom 4 不再讓別人升格。核心角色是副支的料都適用
    #   (secondary,以及與主支垂直的柱面料)。
    if "no_custom4" not in mut:
        promote_custom4(timbers, a, b)
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
def edge_depth(reg, k, lo, hi, start, d):
    """檢查用:軸 k 上離起鋪牆 d 的縫,掃外環牆邊找「縫線上最近的對牆」離起鋪牆的距離:
    與縫平行、在縫的鋪板方向那一側、牆面朝向縫(室內在靠縫那側)、長度方向與縫線的室內段有正長度重疊,取最近的一面。"""
    span = hi - lo
    c = (lo + d - 0.5) if start == "min" else (hi - d + 0.5)  # 往起鋪側偏半 mm:牆剛好在縫上也算在縫前面
    line = reg.section(k, c)
    best = span
    for p0, p1 in reg.outer_edges():
        if p0[k] != p1[k]:
            continue
        e = p0[k]
        if (start == "min" and e <= c) or (start == "max" and e >= c):
            continue
        e0, e1 = sorted((p0[1 - k], p1[1 - k]))
        for y0, y1 in line:
            o0, o1 = max(e0, y0), min(e1, y1)
            if o1 <= o0:
                continue
            probe = e - 0.5 if start == "min" else e + 0.5
            pt = (probe, (o0 + o1) / 2) if k == 0 else ((o0 + o1) / 2, probe)
            if reg.inside(*pt):
                best = min(best, e - lo if start == "min" else hi - e)
    return best


def expected_seam_positions(lo, hi, start, panel, gap, width, reg=None, k=None):
    """G6/G7 另寫一次:從起鋪側量起,第 k 條縫中心距起鋪牆 k·(panel+gap)+panel+gap/2,
    只要下一片板的起點仍在對牆之內就有這條縫;最後一條縫距起鋪牆超過 D-1.5w 時挪到 floor(D-1.5w)。
    D 是「縫線上最近的對牆」離起鋪牆的距離(給了 reg 才算;沒給就用外框深度)。這裡不沿縫線逐段找,
    改成掃外環的牆邊:與縫平行、在縫的鋪板方向那一側、牆面朝向縫(室內在靠縫那側)、長度方向與縫線的室內段有正長度重疊,
    取最近的一面。挪了之後縫線可能變長,重算到穩定;不挪過前一條縫。"""
    span = hi - lo
    half = gap // 2 if start == "min" else gap - gap // 2  # 提案 FT01:正向 P+⌊gap/2⌋,反向 P+⌈gap/2⌉
    dist = []
    j = 0
    while (j + 1) * (panel + gap) < span:
        dist.append(j * (panel + gap) + panel + half)
        j += 1

    def depth(d):
        return span if reg is None else edge_depth(reg, k, lo, hi, start, d)

    for _ in range(8):
        if not dist:
            break
        D = depth(dist[-1])
        if dist[-1] * 2 <= 2 * D - 3 * width:  # 整數比較:d <= D - 1.5w 就不挪
            break
        new = (2 * D - 3 * width) // 2
        if len(dist) > 1 and new <= dist[-2]:
            break
        dist[-1] = new
    return [lo + d for d in dist] if start == "min" else [hi - d for d in dist]


def expected_seam_retreat(seams, reg_o, a, b, start, lo, hi, p):
    """C7 用,另寫一次「板端縫落在牆階短段就往內退」:不看建構出來的角材,直接掃外牆邊。
    短段:與主支平行(固定 A 座標)的外牆面,在凸角那一端被垂直那面牆的邊界材蓋掉 w,剩下 0 < 長 < min_piece 的那段;
    凹角那一端沒有料蓋(另一面牆的邊界材往遠離這條牆線的方向越過凹角)。
    最後一條板端縫的承接帶若碰到短段,就退到 ⌊(起鋪牆到凹角那端) − 1.5w⌋;不退過前一條縫。"""
    w, X, g = p["w"], p["X"], p["gap"]
    minp = p.get("min_piece", w)
    gl, gu = g // 2, g - g // 2
    edges = reg_o.outer_edges()
    n = len(edges)
    shorts = []
    for i, (p0, p1) in enumerate(edges):
        if p0[a] != p1[a]:
            continue
        e = p0[a]
        mid = (p0[b] + p1[b]) / 2
        probe = (e + 0.5, mid) if a == 0 else (mid, e + 0.5)
        room = 1 if reg_o.inside(*probe) else -1  # 室內在這面牆的 +A 或 -A 側
        lo_e, hi_e = sorted((p0[b], p1[b]))
        cut = {lo_e: 0, hi_e: 0}
        reflex = []
        for pt_, nb in ((p0, edges[i - 1][0]), (p1, edges[(i + 1) % n][1])):
            if (nb[a] - pt_[a]) * room > 0:  # 相鄰那面牆往室內那側走:凸角,那面牆的邊界材蓋住這一端 w
                cut[pt_[b]] = w
            else:
                reflex.append(pt_[b])
        u0, u1 = lo_e + cut[lo_e], hi_e - cut[hi_e]
        if 0 < u1 - u0 < minp:
            shorts.append((u0, u1, reflex))
    out = list(seams)
    for _ in range(4):
        if not out:
            break
        last = out[-1]
        hit = [sh for sh in shorts if any(min(x1, sh[1]) > max(x0, sh[0])
                                          for x0, x1 in ((last - gl - X, last - gl), (last + gu, last + gu + X)))]
        if not hit:
            break
        u0, u1, rf = hit[0]
        qs = [q for q in rf if (q <= u0 if start == "min" else q >= u1)]
        if not qs:
            break
        q = max(qs) if start == "min" else min(qs)
        dist = (2 * ((q - lo) if start == "min" else (hi - q)) - 3 * w) // 2
        c_new = lo + dist if start == "min" else hi - dist
        prev = out[-2] if len(out) > 1 else None
        if (c_new >= last if start == "min" else c_new <= last) or (
                prev is not None and (c_new <= prev if start == "min" else c_new >= prev)):
            break
        # 退縫之後再照 G7(縫線上最近的對牆)挪到穩定
        dd = g7_settle(c_new - lo if start == "min" else hi - c_new,
                       None if prev is None else (prev - lo if start == "min" else hi - prev),
                       lambda d_: edge_depth(reg_o, b, lo, hi, start, d_), w)
        out[-1] = lo + dd if start == "min" else hi - dd
    return out


def pos_edge_outer(reg, rect, k):
    """與角材某側面共線、長度區間正重疊的外牆邊(沿軸 k)存在嗎。"""
    span, side = rng(rect, k), rng(rect, 1 - k)
    for p0, p1 in reg.outer_edges():
        if p0[1 - k] == p1[1 - k] and p0[1 - k] in side:
            elo, ehi = sorted((p0[k], p1[k]))
            if min(span[1], ehi) - max(span[0], elo) > 0:
                return True
    return False


def bridged(q, T, minp, k):
    """空檔 q 沿軸 k 夾在兩處角材之間,兩處相距 < minp(R-nosliver 不放料的窄縫):由兩側的料直接承接。
    兩處都要在 q 的另一軸範圍內整片有料(端面外 1 mm 的帶子被角材蓋滿)。只沿軸 k 判斷,不沿另一軸。"""
    o = rng(q, 1 - k)
    lo, hi = rng(q, k)

    def covered(v0, v1):
        return not leftover((v0, o[0], v1, o[1]) if k == 0 else (o[0], v0, o[1], v1), T)

    L = max((rng(t, k)[1] for t in T if lo - minp < rng(t, k)[1] <= lo and covered(rng(t, k)[1] - 1, rng(t, k)[1])), default=None)
    R_ = min((rng(t, k)[0] for t in T if hi <= rng(t, k)[0] < hi + minp and covered(rng(t, k)[0], rng(t, k)[0] + 1)), default=None)
    return L is not None and R_ is not None and R_ - L < minp


# ---------------------------------------------------------------- 檢查(與建構分開,用來抓錯)
def check(res, p):
    reg, a, b = res["region"], res["a"], res["b"]
    w, M, X, g = p["w"], p["M"], p["X"], p["gap"]
    minp = p.get("min_piece", w)
    T = [t["rect"] for t in res["timbers"]]
    fails = []
    # C7 縫位必須等於獨立推算的起鋪結果(G6/G7)。之後的 C3/C4/C5 也改用這組獨立縫位,
    # 不拿建構輸出當「期望」,所以整組錯移但彼此自洽的幾何會在這裡被抓到。
    lay = res["layout"]
    reg_o = Region(reg.rings[0], [])  # 只看外環:柱不是收邊的對牆
    exp_a = expected_seam_positions(reg.bbox[a], reg.bbox[a + 2], lay["a_start"], p["P"], g, w, reg_o, a)
    exp_b = expected_seam_positions(reg.bbox[b], reg.bbox[b + 2], lay["b_start"], p["L"], g, w, reg_o, b)
    exp_b = expected_seam_retreat(exp_b, reg_o, a, b, lay["b_start"], reg.bbox[b], reg.bbox[b + 2], p)
    if sorted(exp_a) != sorted(res["seams_a"]):
        fails.append(dict(check="C7_SEAMS_NOT_FROM_START", axis="A", expected=sorted(exp_a), got=sorted(res["seams_a"])))
    if sorted(exp_b) != sorted(res["seams_b"]):
        fails.append(dict(check="C7_SEAMS_NOT_FROM_START", axis="B", expected=sorted(exp_b), got=sorted(res["seams_b"])))
    # C7b G7 性質(不看演算法,直接驗結果):兩軸的最後一條縫,離「縫線上最近的對牆」都不得少於 1.5w。
    #     例:退縫之後忘了再跑 G7,雙牆階房會剩 13 mm 的收邊板條(#251 審查 98cb7da0)。
    for ax_, k_, seams_, st_ in (("A", a, res["seams_a"], lay["a_start"]), ("B", b, res["seams_b"], lay["b_start"])):
        if not seams_:
            continue
        lo_, hi_ = reg.bbox[k_], reg.bbox[k_ + 2]
        last_ = max(seams_) if st_ == "min" else min(seams_)
        d_ = last_ - lo_ if st_ == "min" else hi_ - last_
        D_ = edge_depth(reg_o, k_, lo_, hi_, st_, d_)
        if d_ * 2 > 2 * D_ - 3 * w:
            fails.append(dict(check="C7_G7_TOO_CLOSE", axis=ax_, seam=last_, opposite_wall_distance=D_ - d_))
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
    # C3 每條面材邊都有支撐,承接寬度 >= X。
    #    唯一的例外是 R-nosliver:板邊沿著邊的方向跨過一條 < min_piece 的窄縫(縫裡不放料),
    #    那一小段由縫兩邊的料承接(bridged 只沿板邊方向判斷,承接寬度不足 X 不在例外內)。
    for cell, qs in by_cell.items():
        for q in qs:
            x0, y0, x1, y1 = q
            sides = [((x0 - 1, y0, x0, y1), lambda s: (x0, s[1], min(x0 + X, x1), s[3]), 1),
                     ((x1, y0, x1 + 1, y1), lambda s: (max(x1 - X, x0), s[1], x1, s[3]), 1),
                     ((x0, y0 - 1, x1, y0), lambda s: (s[0], y0, s[2], min(y0 + X, y1)), 0),
                     ((x0, y1, x1, y1 + 1), lambda s: (s[0], max(y1 - X, y0), s[2], y1), 0)]
            for strip, band, along in sides:
                for seg in leftover(strip, qs):
                    rest = [r for r in leftover(band(seg), T) if not bridged(r, T, minp, along)]
                    if rest:
                        fails.append(dict(check="C3_EDGE_UNSUPPORTED", band=list(band(seg)), gap=list(rest[0])))
    # C4 副支間距:沿 B 軸,角材之間的空檔 <= M - w。
    #    沿室內「整段連續」的區間量(reg.section),不先依輪廓/孔頂點切塊:否則跨過柱或凹角座標的超限空檔
    #    會被切成幾段短的而漏抓(#251 審查 6daa997a 的反例:5000×4000 房、柱 [2415,2715]×[3000,3300]、板長沿 X)。
    for cell in by_cell:
        ar, br = rng(cell, a), rng(cell, b)
        edges = sorted({ar[0], ar[1]} | {v for t in T for v in rng(t, a) if ar[0] < v < ar[1]}
                       | {v for v in reg.coords[a] if ar[0] < v < ar[1]})
        for u0, u1 in zip(edges, edges[1:]):
            um = (u0 + u1) / 2
            for s0, s1 in iv_intersect(reg.section(a, um), [br]):
                if any(rng(t, a)[0] < um < rng(t, a)[1] and rng(t, b)[0] <= s0 and rng(t, b)[1] >= s1 for t in T):
                    continue  # 這一段被一支 B 向角材整段蓋住
                cov = [rng(t, b) for t in T if rng(t, a)[0] < um < rng(t, a)[1]]
                for f0, f1 in iv_subtract([(s0, s1)], cov):
                    # R-nosliver:夾在兩支相距 < min_piece 的平行料之間的窄條,板由兩側的料承接,不量副支間距
                    if f1 - f0 > M - w and not bridged(mk(a, (u0, u1), (f0, f1)), T, minp, a):
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
                if bridged(probe, T, minp, a):
                    continue  # 另一側是 < min_piece 的窄縫(R-nosliver 不放副支),不是可以放副支的跨
                fails.append(dict(check="C9_MARKS_NOT_ALIGNED", main=mt["id"], at=list(br), side=side,
                                  other=[list(s) for s in other if max(s[0], br[0] - w) < min(s[1], br[1] + w)]))
    # C12 記號照同一治具(使用者 2026-10-18 拍板「乙 同一治具 367」;合併平分是協調 agent 推論):這裡另寫一次,不呼叫 jig_marks。
    #     每格從板端縫(沒有板端縫就從起鋪牆)起量 M、2M…;最後一支記號若會碰到格端那支料(板端縫:置中的縫上副支;
    #     牆:貼牆的邊界材),最後兩步合併平分,前一段取上界。格界用獨立推算的 exp_b。
    #     (a) 每支記號副支都要在治具位置上;(b) 治具位置上若有一段 >= min_piece 的室內寬度沒有被別的料擋住,那裡就該有記號。
    lo_m, hi_m = w // 2, w - w // 2
    bb0, bb1 = reg.bbox[b], reg.bbox[b + 2]
    cells_ = list(zip([(bb0, "rc")] + [(e_, "seam") for e_ in sorted(exp_b)], [(e_, "seam") for e_ in sorted(exp_b)] + [(bb1, "rc")]))
    jig = []
    low_start = lay["b_start"] == "min"
    for (q0, t0), (q1, t1) in cells_:
        if t0 == "seam" and (t1 != "seam" or low_start):
            org, sg = q0, 1
        elif t1 == "seam":
            org, sg = q1, -1
        else:
            org, sg = (q0, 1) if low_start else (q1, -1)
        steps = -(-(q1 - q0) // M)  # ⌈L/M⌉
        pos = [org + sg * M * j for j in range(1, steps)]
        if pos:
            rem = (q1 - q0) - M * (steps - 1)
            far, fk = (q1, t1) if sg > 0 else (q0, t0)
            fb = (far - lo_m, far + hi_m) if fk == "seam" else ((far - w, far) if sg > 0 else (far, far + w))
            if min(pos[-1] + hi_m, fb[1]) > max(pos[-1] - lo_m, fb[0]):
                pos[-1] = org + sg * (M * (steps - 2) + -(-(M + rem) // 2))
        jig += pos
    jig_set = set(jig)
    gl, gu = g // 2, g - g // 2
    mid_ = lambda t: rng(t["rect"], b)[0] + lo_m  # 角材矩形的中線位置(不看 at、不看 role)
    secs_ = [t for t in res["timbers"] if t["kind"] == "secondary"]
    nonsec_ = [t for t in res["timbers"] if t["kind"] != "secondary"]
    a_ov = lambda r1, r2: min(rng(r1, a)[1], rng(r2, a)[1]) > max(rng(r1, a)[0], rng(r2, a)[0])
    b_ov = lambda r1, iv: min(rng(r1, b)[1], iv[1]) > max(rng(r1, b)[0], iv[0])

    def seam_rest(t, e):
        """縫 e 兩側板邊承接帶中,在這一條(t 的 A 範圍)室內、又沒有非副支料蓋住的部分:這部分要靠縫上副支。"""
        ta = rng(t["rect"], a)
        um = (ta[0] + ta[1]) / 2
        cov = [rng(q["rect"], b) for q in nonsec_ if rng(q["rect"], a)[0] <= ta[0] and ta[1] <= rng(q["rect"], a)[1]]
        rest = []
        for x0, x1 in ((e - gl - X, e - gl), (e + gu, e + gu + X)):
            rest += iv_intersect(iv_subtract([(x0, x1)], cov), reg.section(a, um))
        return rest

    def butts(t):
        """t 一端貼著的非副支料(同一條有 A 向重疊、B 向端面相接)。"""
        tb = rng(t["rect"], b)
        return [q for q in nonsec_ if a_ov(q["rect"], t["rect"]) and (rng(q["rect"], b)[0] == tb[1] or rng(q["rect"], b)[1] == tb[0])]

    def needed(t):
        """拿掉 t,它那一條沿 B 軸的空檔就超過 M − w。"""
        ta, tb = rng(t["rect"], a), rng(t["rect"], b)
        um = (ta[0] + ta[1]) / 2
        cov = [rng(q["rect"], b) for q in res["timbers"] if q is not t and rng(q["rect"], a)[0] < um < rng(q["rect"], a)[1]]
        run = [iv for iv in iv_subtract(reg.section(a, um), cov) if iv[0] <= tb[0] and tb[1] <= iv[1]]
        return bool(run) and run[0][1] - run[0][0] > M - w

    def kind_of(t):
        """不在治具記號上的副支是哪一種(只看幾何):'seam' 真的在縫上、'seam_end' 依 P-180 貼著擋料的縫上副支、'fill' 補位副支,都不是就 None。"""
        tb = rng(t["rect"], b)
        for e_ in exp_b:
            rest = seam_rest(t, e_)
            if rest and all(tb[0] <= x0 and x1 <= tb[1] for x0, x1 in rest):
                return "seam"
        for q in butts(t):
            touch = rng(q["rect"], b)[0] if rng(q["rect"], b)[0] == tb[1] else rng(q["rect"], b)[1]
            for e_ in exp_b:
                if abs(e_ - touch) < w and not seam_rest(t, e_):
                    return "seam_end"
            for j_ in jig:
                band_ = (j_ - lo_m, j_ + hi_m)
                if abs(mid_(t) - j_) < w and b_ov(q["rect"], band_):
                    return "fill"  # 那支治具記號的位置確實被這支擋料佔住(放不下),補位副支貼著它
        return None

    on_jig = lambda t: mid_(t) in jig_set
    marks_ = [t for t in secs_ if t.get("role") == "mark"]
    for t in marks_:
        if not on_jig(t):
            fails.append(dict(check="C12_MARK_OFF_JIG", id=t["id"], at=mid_(t)))
    # C13 不在治具記號上的副支(不看 role 標籤):(c) 位置要合規則——真的在縫上、依 P-180 貼著擋料的縫上副支、
    #     或貼著擋料的補位副支(那支治具記號確實被擋料佔住);(a) 後兩種要「必要」:拿掉它空檔就超過 M − w;
    #     (b) 都不得與同一條的其他副支雙拼(至少留 w)。
    kinds_ = {}
    for t in secs_:
        if on_jig(t):
            continue
        k_ = kinds_[t["id"]] = kind_of(t)
        if k_ is None:
            fails.append(dict(check="C13_EXTRA_OFF_RULE", id=t["id"], role=t.get("role"), rect=list(t["rect"])))
        if k_ != "seam" and not needed(t):
            fails.append(dict(check="C13_EXTRA_UNNEEDED", id=t["id"], role=t.get("role"), rect=list(t["rect"])))
        tb = rng(t["rect"], b)
        for q in secs_:
            if q is t or not a_ov(q["rect"], t["rect"]):
                continue
            qb = rng(q["rect"], b)
            if max(qb[0] - tb[1], tb[0] - qb[1]) < w:
                fails.append(dict(check="C13_EXTRA_DOUBLED", id=t["id"], with_=q["id"]))
    # C12 (b) 每一條都驗:治具位置上,扣掉合法的擋料(非副支料、真的在縫上或依 P-180 貼擋料的縫上副支)
    #     與已經在那裡的記號,還剩 >= min_piece 的室內寬度,那裡就少了記號。補位副支與其他副支不算擋料。
    legit_ = [t for t in secs_ if kinds_.get(t["id"]) in ("seam", "seam_end")]
    for e_ in sorted(jig_set):
        band_ = (e_ - lo_m, e_ + hi_m)
        free_ = reg.strip_set(b, *band_)
        blk = [rng(t["rect"], a) for t in nonsec_ + legit_ if b_ov(t["rect"], band_)]
        blk += [rng(t["rect"], a) for t in secs_ if on_jig(t) and mid_(t) == e_]
        room_ = [iv for iv in iv_subtract(free_, blk) if iv[1] - iv[0] >= minp]
        if room_:
            fails.append(dict(check="C12_JIG_MARK_MISSING", at=e_, room=[list(iv) for iv in room_[:2]]))
    # C10 R-nosliver:任何料都不得短於 min_piece。副支與柱面料:使用者 2026-10-18 的決定(選項原文「不放(短於 27 一律不放)」);
    #     牆面上的料比照,是由「一律」推得的推論,不是使用者原話。
    for t in res["timbers"]:
        k = b if t["kind"] in ("main", "rc_parallel") else a
        ln = rng(t["rect"], k)[1] - rng(t["rect"], k)[0]
        if ln < minp:
            fails.append(dict(check="C10_SHORT_PIECE", id=t["id"], kind=t["kind"], length=ln, min_piece=minp))
    # C11 R-butt:主支和相鄰平行料(主支、沿牆料、孔邊料、併料)之間有 0 < 間隙,而把主支平移這段間隙後,
    #     縫兩側板邊承接仍 >= X(縫位用獨立推算的 exp_a 驗過的那條),就必須貼住;已經貼住某一支就不再要求。
    gl, gu = g // 2, g - g // 2
    par = [t for t in res["timbers"] if t["kind"] in ("main", "rc_parallel")]
    for t in [t for t in res["timbers"] if t["kind"] == "main"]:
        ma, mb = rng(t["rect"], a), rng(t["rect"], b)
        c = t["seam"]
        near, touching = {}, False
        for q in par:
            qa, qb = rng(q["rect"], a), rng(q["rect"], b)
            if q is t or min(qb[1], mb[1]) - max(qb[0], mb[0]) <= 0:
                continue
            if qa[1] <= ma[0]:
                d, gap_ = -1, ma[0] - qa[1]
            elif qa[0] >= ma[1]:
                d, gap_ = 1, qa[0] - ma[1]
            else:
                continue
            touching |= gap_ == 0
            near[d] = min(near.get(d, gap_), gap_)
        if touching:
            continue
        for d, gap_ in sorted(near.items()):
            if ma[0] + d * gap_ <= c - gl - X and ma[1] + d * gap_ >= c + gu + X:
                fails.append(dict(check="C11_MAIN_NOT_BUTTED", id=t["id"], gap=gap_, side=d, seam=c))
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
    #   C8d I19 數值比較:除了外牆 boundary(端面由 C8b 管),每支料每個端面所頂擋面的擁有者,
    #       優先級必須嚴格小於自己。擋面落在延伸段上以 2 計(I22);孔邊、柱面 = 0(端面外是 RC,沒有擁有者)。
    #       優先級照核心宣告:boundary 1、主支與沿牆/孔邊料(primary)2、副支與柱面料 3、custom 明寫(build 的 core_role/priority)。
    #       這條補上 2026-10-18 以前漏掉的「端面頂 custom 側面」比較(副支 3 頂 custom 3 會被核心以 V_CUT_PRIORITY 拒絕)。
    def core_prio(t):
        if t.get("core_role") == "custom":
            return t["priority"]
        if t["kind"] == "boundary":
            return 1 if pos_edge_outer(reg, t["rect"], a) else 3
        return {"main": 2, "rc_parallel": 2, "secondary": 3}[t["kind"]]

    for t in res["timbers"]:
        if t["kind"] == "boundary" and pos_edge_outer(reg, t["rect"], a):
            continue
        k = b if t["kind"] in ("main", "rc_parallel") else a
        mine = core_prio(t)
        for at, slab in end_slabs(t["rect"], k):
            indoor = leftover(slab, leftover(slab, R))
            for s in res["timbers"]:
                contact = [(max(q[0], s["rect"][0]), max(q[1], s["rect"][1]), min(q[2], s["rect"][2]), min(q[3], s["rect"][3]))
                           for q in indoor if s is not t and overlap(q, s["rect"])]
                if not contact:
                    continue
                theirs = core_prio(s)
                if any(overlap(cq, x) for cq in contact for x in exts):
                    theirs = max(theirs, 2)
                if not theirs < mine:
                    fails.append(dict(check="C8_I19_PRIORITY", id=t["id"], end=at, on=s["id"], mine=mine, theirs=theirs))
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
                              **{k: v for k, v in t.items() if k in ("seam", "at", "role", "rc_line", "core_role", "priority")})
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
