"""framing_oracle 的自我測試:(1) 突變必須被檢查抓到;(2) 矩形房各種尺寸都必須可施工且全數通過檢查。"""
import json
import sys
import time

import framing_oracle as fo

spec = json.load(open("rooms.json", encoding="utf-8"))
p = spec["params"]
R = spec["rooms"]
LT_Y = dict(A="x", a_start="min", b_start="min")
RECT = lambda W, H: {"outer": [[0, 0], [W, 0], [W, H], [0, H]]}

failed = False
# (1) 突變:拿掉某條規則,對應的檢查必須轉紅
MUTANTS = [
    ("no_sliver", RECT(3700, 2000), "C1_OVERLAP", "拿掉挪縫規則:3700 寬時最後一支主支撞到對牆角材"),
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
    print(f"[{'紅' if ok else '沒抓到!'}] {mut:18s} 預期 {want:22s} 實得 {sorted(got)}  {why}")

# 未突變的同一組必須全綠(對照組)
for name in ("F3次臥", "F5廚房"):
    res = fo.build(R[name], LT_Y, p)
    fails = fo.check(res, p)
    ok = not res["conflicts"] and not fails
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] 對照 {name} 左上 Y")

# (2) 掃描:矩形房每一個 mm 寬度/深度都要可施工
t0 = time.time()
bad = []
cases = [(W, 2500) for W in range(300, 4001)] + [(2000, H) for H in range(300, 6001, 1)]
for W, H in cases:
    for l in (LT_Y, dict(A="x", a_start="max", b_start="max")):
        res = fo.build(RECT(W, H), l, p)
        fails = [] if res["conflicts"] else fo.check(res, p)
        if res["conflicts"] or fails:
            bad.append((W, H, fo.layout_name(l), sorted({c["code"] for c in res["conflicts"]}), sorted({f["check"] for f in fails})))
print(f"掃描 {len(cases) * 2} 個矩形房案例,{time.time() - t0:.0f} 秒;不可施工或檢查失敗 {len(bad)} 個")
for b in bad[:30]:
    print("   ", b)
failed |= bool(bad)
sys.exit(1 if failed else 0)
