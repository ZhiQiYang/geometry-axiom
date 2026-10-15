"""framing_oracle 的自我測試。
(1) 突變:拿掉或弄偏某條規則,對應的檢查必須轉紅;未突變的對照組必須全綠。
(2) 標準答案:F1–F5 與兩個挪縫例子、8 種排法的輸出,必須與 oracle-golden.json 逐支相同。
(3) 掃描:矩形房。
    快速(預設,約 1–2 分鐘):
      - 一維逐 mm:寬 300–4000 × 深 2500,以及寬 2000 × 深 300–6000,只跑左上起鋪、板長沿 Y。
      - 二維 × 8 種排法:寬取 917k+{-43…-39,-1…2}(k=1–4,挪縫臨界帶)與每 331 mm;
        深取 1832k+{-43…-39,-1…2}(k=1–3)與每 617 mm。
    完整(--full,約 10 分鐘以上):
      - 一維逐 mm 掃描改跑全部 8 種排法。
      - 二維改為寬 917k±45、深 1832k±45 的整段邊界帶,加上每 97/211 mm 的網格。
用法: python selftest.py [--full]
"""
import json
import sys
import time
from pathlib import Path

import framing_oracle as fo

HERE = Path(__file__).resolve().parent
spec = json.load(open(HERE / "rooms.json", encoding="utf-8"))
p = spec["params"]
R = spec["rooms"]
LT_Y = dict(A="x", a_start="min", b_start="min")
RECT = lambda W, H: {"outer": [[0, 0], [W, 0], [W, H], [0, H]]}
FULL = "--full" in sys.argv

failed = False
# (1) 突變
MUTANTS = [
    ("no_sliver", RECT(3700, 2000), "C7_SEAMS_NOT_FROM_START", "拿掉挪縫規則:3700 寬時最後一條縫沒挪"),
    ("shift_origin", R["F3次臥"], "C7_SEAMS_NOT_FROM_START", "起鋪點整組錯移 20 mm,其餘幾何照樣自洽"),
    ("floor_n", R["F3次臥"], "C4_SPACING", "副支格數改用無條件捨去:間距超過上限"),
    ("drop_mark", R["F3次臥"], "C4_SPACING", "每格少放第一支記號副支:間距超過上限"),
    ("no_column_strips", R["F5廚房"], "C3_EDGE_UNSUPPORTED", "柱邊不放角材:柱邊面材沒有支撐"),
    ("shift_main", R["F3次臥"], "C3_EDGE_UNSUPPORTED", "主支偏離板縫 15 mm:板縫沒有支撐"),
    ("allow_split", R["F2主臥"], "C5_MAIN_NOT_SINGLE", "允許主支被凸出切成兩段"),
]
for mut, room, want, why in MUTANTS:
    res = fo.build(room, LT_Y, p, frozenset({mut, "skip_conflict_scan"}))
    got = {f["check"] for f in fo.check(res, p)}
    ok = want in got
    failed |= not ok
    print(f"[{'紅' if ok else '沒抓到!'}] {mut:18s} 預期 {want:24s} 實得 {sorted(got)}  {why}")
for name in ("F3次臥", "F5廚房"):
    res = fo.build(R[name], LT_Y, p)
    fails = fo.check(res, p)
    ok = not res["conflicts"] and not fails
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] 對照 {name} 左上 Y")

# (2) 標準答案
sys.path.insert(0, str(HERE))
import make_golden  # noqa: E402

golden = json.load(open(HERE / "oracle-golden.json", encoding="utf-8"))
now = json.loads(json.dumps(make_golden.snapshot(spec), ensure_ascii=False, sort_keys=True))
diff = []
for name, g in golden["rooms"].items():
    for gl, nl in zip(g["layouts"], now["rooms"].get(name, {}).get("layouts", [])):
        if gl != nl:
            diff.append((name, gl["name"]))
if set(golden["rooms"]) != set(now["rooms"]):
    diff.append(("房間清單不同", sorted(set(golden["rooms"]) ^ set(now["rooms"]))))
failed |= bool(diff)
print(f"[{'綠' if not diff else '錯!'}] 標準答案逐支比對:{len(golden['rooms'])} 個房間 × 8 種排法,不一致 {len(diff)}")
for d in diff[:20]:
    print("   ", d)

# (3) 掃描
t0 = time.time()
bad = []
layouts = fo.LAYOUTS if FULL else [LT_Y]
cases = [(W, 2500) for W in range(300, 4001)] + [(2000, H) for H in range(300, 6001)]
runs = 0
for W, H in cases:
    for l in layouts:
        runs += 1
        res = fo.build(RECT(W, H), l, p)
        fails = [] if res["conflicts"] else fo.check(res, p)
        if res["conflicts"] or fails:
            bad.append((W, H, fo.layout_name(l), sorted({c["code"] for c in res["conflicts"]}), sorted({f["check"] for f in fails})))
band = (range(-45, 46) if FULL else (-43, -42, -41, -40, -39, -1, 0, 1, 2))
edge_w = sorted({k * 917 + d for k in range(1, 5) for d in band if 300 <= k * 917 + d <= 4000}
                | set(range(300, 4001, 97 if FULL else 331)))
edge_h = sorted({k * 1832 + d for k in range(1, 4) for d in band if 300 <= k * 1832 + d <= 6000}
                | set(range(300, 6001, 211 if FULL else 617)))
for W in edge_w:
    for H in edge_h:
        for l in fo.LAYOUTS:
            runs += 1
            res = fo.build(RECT(W, H), l, p)
            fails = [] if res["conflicts"] else fo.check(res, p)
            if res["conflicts"] or fails:
                bad.append((W, H, fo.layout_name(l), sorted({c["code"] for c in res["conflicts"]}), sorted({f["check"] for f in fails})))
print(f"掃描 {runs} 次矩形房建構({'完整' if FULL else '快速'}),{time.time() - t0:.0f} 秒;不可施工或檢查失敗 {len(bad)} 個")
for b in bad[:30]:
    print("   ", b)
failed |= bool(bad)
sys.exit(1 if failed else 0)
