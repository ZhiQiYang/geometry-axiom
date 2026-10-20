"""轉置對稱掃描(#319 第三項:掃一遍現有房型,看有沒有缺陷被 C3 的分塊截斷藏住)。草稿,這一輪沒有執行。

原理:x、y 對調(TRANSPOSE)是保持朝向的對稱(不是鏡射的 ⌊w/2⌋、⌈w/2⌉ 問題),所以房間 R 用排法 l 的結果,
要和轉置房間 T(R) 用轉置排法 T(l)(A 軸 x↔y 互換,a_start、b_start 不變)的結果完全一樣:
  - 可施工與否、衝突碼相同;
  - 縫位相同(R 的主支縫沿 y 的座標 = T(R) 的主支縫沿 x 的座標);
  - 可施工的檢查失敗碼相同。
C3 的承接帶被 x 分塊截斷時,一邊(承接帶沿 x)看不到的缺陷、另一邊(承接帶沿 y)看得到,兩邊的檢查失敗碼就不一樣。
這是不需要手算期望值的獨立判準(對稱性),補上〈板長沿 Y 的對照房太少〉的洞。

用法(WSL 空下來之後;單獨跑,不要和正式驗收並行):
    ORACLE_DIR=<oracle 目錄> python tp_scan.py [--quick | --full]
    不帶參數 = 抽樣(每第 5 間凹角房、每第 4 間牆階房、P-182 四族各取少量);--quick 取全部凹角與牆階房;--full 加上 P-182 四族全量。
輸出:不一致的 (房間, 排法, 差異) 前 30 筆與總數;全部一致則 exit 0。
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(os.environ.get("ORACLE_DIR", Path(__file__).resolve().parent)).resolve()
sys.path.insert(0, str(HERE))
import framing_oracle as fo  # noqa: E402

p = json.load(open(HERE / "rooms.json", encoding="utf-8"))["params"]
MODE = "full" if "--full" in sys.argv else "quick" if "--quick" in sys.argv else "ci"


def TRANSPOSE(room):
    sw = lambda q: [q[1], q[0]]
    out = dict(room, outer=[sw(q) for q in reversed(room["outer"])])
    if room.get("holes"):
        out["holes"] = [[sw(q) for q in reversed(h)] for h in room["holes"]]
    return out


def T_LAYOUT(l):
    return dict(A="x" if l["A"] == "y" else "y", a_start=l["a_start"], b_start=l["b_start"])


LROOM = lambda W, H, cw, ch: {"outer": [[0, 0], [W, 0], [W, H - ch], [W - cw, H - ch], [W - cw, H], [0, H]]}
ALCOVE = lambda W, H, y0, y1, dep: {"outer": [[dep, 0], [W, 0], [W, H], [dep, H], [dep, y1], [0, y1], [0, y0], [dep, y0]]}
COLUMN = lambda W, H, x, y, cs: {"outer": [[0, 0], [W, 0], [W, H], [0, H]], "holes": [[[x, y], [x + cs, y], [x + cs, y + cs], [x, y + cs]]]}
PILW = lambda W, H, y0, y1, dx: {"outer": [[0, 0], [W, 0], [W, H], [0, H], [0, y1], [dx, y1], [dx, y0], [0, y0]]}

rooms = []
# 凹角、壁龕、獨立柱(和 selftest 的 reflex_rooms 同一族)
refl = [(f"L:{W},{H},{cw},{ch}", LROOM(W, H, cw, ch)) for W in (3000, 4100, 5000) for H in (2600, 3700, 4800)
        for cw in range(300, W - 299, 457) for ch in range(300, H - 299, 613)]
refl += [(f"A:{W},{y0},{L},{dep}", ALCOVE(W, 3000, y0, y0 + L, dep)) for W in (3000, 4400) for y0 in (400, 1000, 1700)
         for L in (400, 900) for dep in (300, 600) if y0 + L <= 2600]
refl += [(f"C:{W},{H},{x},{y},{cs}", COLUMN(W, H, x, y, cs)) for W, H in ((3600, 3000), (5000, 4200)) for cs in (300, 450)
         for x in range(500, W - cs - 499, 433) for y in range(500, H - cs - 499, 521)]
# 牆階 1–100 mm 與雙牆階(和 selftest 的 step_rooms 同一族)
step = ([(f"L_ch:{s}", LROOM(4100, 3700, 1500, s)) for s in range(1, 101)] + [(f"L_cw:{s}", LROOM(4100, 3700, s, 1200)) for s in range(1, 101)]
        + [(f"alcove:{s}", ALCOVE(4100, 3000, 1000, 1900, s)) for s in range(1, 101)]
        + [(f"DS:{s1},{s2}", {"outer": [[0, 0], [4100, 0], [4100, s2], [3300, s2], [3300, s1], [2600, s1], [2600, 3700], [0, 3700]]})
           for s1 in range(3604, 3700, 9) for s2 in range(s1 - 88, s1, 9)])
# 縫離 x 分塊邊界不到 X 的房間才會受 #319 影響:另外造一族,板端縫 1831、3663(與右起鋪的 W − 1831、W − 3663)與主支縫 916k+… 貼著牆階垂直牆 x = 縫 ± 2…9
near = []
for W in (3600, 4100):
    for seam in (916, 1833, 2750, 1831, 3663, W - 916, W - 1833, W - 2750, W - 1831, W - 3663):
        for d in range(-9, 10):
            xs = seam + d
            if 300 < xs < W - 300:
                near.append((f"near:{W},{xs}", LROOM(W, 3700, W - xs, 1200)))
                near.append((f"nearP:{W},{xs}", PILW(W, 3200, 1000, 1900, xs)))  # 壁柱寬 = xs(垂直牆在 x = xs)
if MODE == "ci":
    refl, step = refl[::5], step[::4]
    near = near[::7]
rooms = refl + step + near
if MODE == "full":  # P-182 四族的全量太大,這裡只放壁柱加柱一族(其餘用 selftest 的 P-182 掃描)
    for y0 in range(2741, 2750):
        for x0 in (400, 1000, 2000, 3000):
            rooms.append((f"t14:{y0},{x0}", dict(PILW(4100, 3200, y0, 2900, 200), holes=[[[x0, 2650], [x0 + 300, 2650], [x0 + 300, 2850], [x0, 2850]]])))

bad, n = [], 0
for rid, room in rooms:
    troom = TRANSPOSE(room)
    for l in fo.LAYOUTS:
        n += 1
        out = []
        for rm, ly in ((room, l), (troom, T_LAYOUT(l))):
            try:
                r = fo.build(rm, ly, p)
                f = [] if r["conflicts"] else fo.check(r, p)
                out.append((sorted({c["code"] for c in r["conflicts"]}), sorted(r["seams_a"]), sorted(r["seams_b"]), sorted({x["check"] for x in f})))
            except AssertionError as e:
                out.append(("CRASHED", str(e) or "AssertionError"))
        if out[0] != out[1]:
            bad.append((rid, fo.layout_name(l), out[0], out[1]))
print(f"轉置對稱掃描({MODE}):{len(rooms)} 間 × 8 種排法 = {n} 組,不一致 {len(bad)}")
for x in bad[:30]:
    print("   ", x)
sys.exit(1 if bad else 0)
