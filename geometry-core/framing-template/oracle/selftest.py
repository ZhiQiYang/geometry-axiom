"""framing_oracle 的自我測試。
(1) 突變:拿掉或弄偏某條規則,對應的檢查必須轉紅;未突變的對照組必須全綠。
    另跑 no_custom4(不套副支 custom 4):F1、F2 那 14 種排法都要被 C8_I19_PRIORITY 抓到,不多不少。
    剛好 min_piece(27 mm)的副支與柱面料必須放(T27 房);custom 4 的柱面料分支與寬向條件用合成案例驗。
(3c) 牆階 1–100 mm 的 L 形與壁龕 300 間 × 8 種排法,可施工的排法都要通過全部檢查。
用法另有 --mutants-only:只跑 (1)(2),跳過掃描。
(2) 標準答案:F1–F5 與三個額外例子、8 種排法的輸出,必須與 oracle-golden.json 逐支相同。
(3b) 凹角、壁龕、獨立柱房 579 間與奇數縫寬矩形房,可施工的排法都要通過全部檢查。
(3) 掃描:矩形房。
    快速(預設,約 1–2 分鐘):
      - 一維逐 mm:寬 300–4000 × 深 2500,以及寬 2000 × 深 300–6000,只跑左上起鋪、板長沿 Y。
      - 二維 × 8 種排法:寬取 917k+{-43…-39,-1…2}(k=1–4,挪縫臨界帶)與每 331 mm;
        深取 1832k+{-43…-39,-1…2}(k=1–3)與每 617 mm。
    完整(--full,約 10 分鐘以上):
      - 一維逐 mm 掃描改跑全部 8 種排法。
      - 二維改為寬 917k±45、深 1832k±45 的整段邊界帶,加上每 97/211 mm 的網格。
用法: python selftest.py [--full | --mutants-only]
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
MUTANTS_ONLY = "--mutants-only" in sys.argv  # 只跑 (1) 突變與 (2) 標準答案,跳過掃描(檢查紅燈用)
# 剛好 27 mm 的邊界(R-nosliver「< min_piece 不放」,剛好 min_piece 要放):左上起鋪板長沿 Y 的第二支主支 [1820,1847]
# 離柱左面沿柱料 [1766,1793] 剛好 27 mm(這一跨的副支長 27),主支切過柱上下面的柱面料,左邊剩 [1793,1820] 剛好 27 mm。
T27 = {"outer": [[0, 0], [3600, 0], [3600, 3000], [0, 3000]], "holes": [[[1793, 1200], [2093, 1200], [2093, 1500], [1793, 1500]]]}
# 20 mm 牆階(#251 審查 60785906 的反例):牆 y=3700 的沿牆料寬 27,比牆階寬,端面有 7 mm 落在牆階邊界材越過凹角的延伸段上
STEP20 = {"outer": [[0, 0], [4100, 0], [4100, 3680], [2600, 3680], [2600, 3700], [0, 3700]]}
# 40 mm 牆階:牆階面 y 3660–3700 被 y=3700 牆的邊界材蓋掉 27 mm,只剩 13 mm,照「短於 27 一律不放」不放沿牆料
STEP40 = {"outer": [[0, 0], [4100, 0], [4100, 3660], [2600, 3660], [2600, 3700], [0, 3700]]}
# 45 mm 牆階:牆階牆 y=3655 在縫 3659 前面,縫線不伸進淺的那段,FT02 不挪;用來留住兩類仍不可施工的例子
STEP45 = {"outer": [[0, 0], [4100, 0], [4100, 3655], [2600, 3655], [2600, 3700], [0, 3700]]}

failed = False
# (1) 突變
MUTANTS = [
    ("no_sliver", RECT(3700, 2000), "C7_SEAMS_NOT_FROM_START", "拿掉挪縫規則:3700 寬時最後一條縫沒挪"),
    ("shift_origin", R["F3次臥"], "C7_SEAMS_NOT_FROM_START", "起鋪點整組錯移 20 mm,其餘幾何照樣自洽"),
    ("floor_n", R["F3次臥"], "C4_SPACING", "副支格數改用無條件捨去:間距超過上限"),
    ("drop_mark", R["F3次臥"], "C4_SPACING", "每格少放第一支記號副支:間距超過上限"),
    ("no_column_strips", R["F5廚房"], "C3_EDGE_UNSUPPORTED", "柱邊不放角材:柱邊面材沒有支撐"),
    ("shift_main", R["F3次臥"], "C3_EDGE_UNSUPPORTED", "主支偏離板縫 15 mm:板縫沒有支撐"),
    ("split_main_mid", R["F3次臥"], "C5_MAIN_GAP", "主支在室內中間斷開 100 mm(不是停在 RC)"),
    ("split_main_mid", R["F3次臥"], "C5_MAIN_END_NOT_ON_RC", "同上:斷開處的端面不在 RC 或外牆邊界材上"),
    ("seam_centered", R["F1客廳"], "C1_OVERLAP", "板端縫副支一律置中、不貼著 RC 角材挪:撞到凹角邊界材", "左下起鋪,板長沿Y"),
    ("misalign_marks", R["F3次臥"], "C9_MARKS_NOT_ALIGNED", "第一支主支右側的記號副支整組偏 20 mm:兩側不對齊"),
    ("fixed_n", R["F2主臥"], "C4_SPACING", "記號撞到壁柱邊界材時不加密,只拿掉:間距超過上限", "左上起鋪,板長沿Y"),
    ("no_main_shift", R["F1客廳"], "C1_OVERLAP", "主支不平移:撞到內牆的沿牆角材", "右上起鋪,板長沿Y"),
    ("no_doubling", R["F1客廳"], "C3_EDGE_UNSUPPORTED", "主支平移 8 mm 後不補併料:另一側整片板邊承接不足", "右上起鋪,板長沿Y"),
    ("no_end_push", {"outer": [[0, 0], [3000, 0], [3000, 948], [2700, 948], [2700, 3700], [0, 3700]]}, "C8_MAIN_ON_EXTENSION",
     "主支跨在凹角牆線上、不推進牆段:端面一部分落在延伸段", "左下起鋪,板長沿X"),
    ("gap_floor_both", dict(RECT(3700, 4000), params={"gap": 3}), "C7_SEAMS_NOT_FROM_START",
     "縫寬 3、反向起鋪仍取下界:首縫偏 1 mm(提案 FT01 反向取上界)", "右上起鋪,板長沿Y"),
    ("one_sided_delete", R["F3次臥"], "C9_MARKS_NOT_ALIGNED", "第一支主支右側少一支記號副支,左側那支還在"),
    ("drop_mark_row_at_column", {"outer": [[0, 0], [5000, 0], [5000, 4000], [0, 4000]], "holes": [[[2415, 3000], [2715, 3000], [2715, 3300], [2415, 3300]]]},
     "C4_SPACING", "柱子 x 座標附近整排記號被拿掉(兩側一起):空檔跨過柱的座標,舊 C4 會切段漏抓", "左上起鋪,板長沿X"),
    ("rc_through_reflex", R["F1客廳"], "C8_I22_NON_BOUNDARY_EXTENDS", "凹角處沿牆料穿過凹角(舊排法):核心 I22 不接受"),
    ("rc_through_reflex", R["F1客廳"], "C8_I19_BOUNDARY_END", "同上:凹角另一面的邊界材端面頂到沿牆料,核心 I19 不接受"),
    ("no_boundary_extension", R["F1客廳"], "C6_END_NOT_ON_TIMBER", "凹角處邊界材不延伸:沿牆料端面懸空"),
    ("no_r_butt", RECT(3700, 2000), "C11_MAIN_NOT_BUTTED", "拿掉 R-butt:挪縫後主支離左牆沿牆料 1 mm,沒有貼住", "右上起鋪,板長沿Y"),
    ("no_r_butt", R["F5廚房"], "C11_MAIN_NOT_BUTTED", "拿掉 R-butt:主支離柱面沿柱料 2 mm,沒有貼住", "左下起鋪,板長沿X"),
    ("allow_short_pieces", R["F5廚房"], "C10_SHORT_PIECE", "拿掉 R-nosliver:沿柱料與主支之間 23 mm 的縫裡放 23 mm 長的副支與柱面料", "左上起鋪,板長沿X"),
    ("allow_short_pieces", R["F1客廳"], "C10_SHORT_PIECE", "拿掉 R-nosliver:沿柱料與主支之間 10 mm 的縫裡放 10 mm 長的副支", "左上起鋪,板長沿Y"),
    ("nosliver_too_wide", R["F1客廳"], "C4_SPACING", "R-nosliver 門檻誤設 100:93 mm 寬的跨也不放副支(窄縫豁免只到 min_piece)", "左上起鋪,板長沿X"),
    ("nosliver_too_wide", R["F1客廳"], "C3_EDGE_UNSUPPORTED", "同上:板端縫跨過 93 mm 的空檔沒有承接", "左上起鋪,板長沿X"),
    ("no_custom4", R["F2主臥"], "C8_I19_PRIORITY", "不套 custom 4:副支(3)端面頂壁柱沿牆料(custom 3),I19 要嚴格小於", "左上起鋪,板長沿Y"),
    ("sliver_le", T27, "C4_SPACING", "R-nosliver 邊界誤寫成 <=:剛好 27 mm 的跨不放副支;檢查端 bridged 若也誤寫成 <= 就抓不到"),
    ("sliver_le", T27, "C3_EDGE_UNSUPPORTED", "同上:剛好 27 mm 的柱面料也不放,柱面與板端縫邊沒有承接"),
    ("no_ext_custom3", STEP20, "C8_I19_PRIORITY", "牆階 20 mm:沿牆料端面頂延伸段卻沒宣告 custom 3(primary 2 頂延伸段 2)", "左下起鋪,板長沿X"),
    ("short_face_conflict", STEP40, "C10_SHORT_PIECE", "牆階 40 mm:牆階面只剩 13 mm 也放沿牆料(不照「短於 27 一律不放」)", "左下起鋪,板長沿Y"),
    ("bbox_ft02", STEP20, "C7_SEAMS_NOT_FROM_START", "FT02 退回照外框挪縫(3659):縫線上最近的對牆是 x>2600 的 y=3680 牆,應挪到 3639", "左上起鋪,板長沿X"),
    ("bbox_ft02", STEP40, "C7_SEAMS_NOT_FROM_START", "同上,板端縫(B 軸):40 mm 牆階應挪到 3619", "左上起鋪,板長沿Y"),
    ("bbox_ft02+no_push_fallback", STEP40, "C1_OVERLAP", "照外框挪縫時,讓開牆料的平移撞到 y=3700 的牆料,沒有退回置中", "左上起鋪,板長沿X"),
    ("no_seam_retreat", STEP45, "C7_SEAMS_NOT_FROM_START", "45 mm 牆階:板端縫 3659 的承接帶落在牆階面沒料的 18 mm 裡,沒有往內退到 3614", "左上起鋪,板長沿Y"),
]
for mut, room, want, why, *lay in MUTANTS:
    lt = next(l for l in fo.LAYOUTS if fo.layout_name(l) == lay[0]) if lay else LT_Y
    pp = dict(p, **room.get("params", {}))
    res = fo.build(room, lt, pp, frozenset(set(mut.split("+")) | {"skip_conflict_scan"}))
    got = {f["check"] for f in fo.check(res, pp)}
    ok = want in got
    failed |= not ok
    print(f"[{'紅' if ok else '沒抓到!'}] {mut:18s} 預期 {want:24s} 實得 {sorted(got)}  {why}")
# 凹角沿牆料/併料的排序(使用者 2026-10-18 拍板,決策佇列選項 C):不套 custom 4 時,端面頂 custom 3 的副支
# 在 I19 數值比較(C8_I19_PRIORITY)轉紅。F1 全部 8 種、F2 的 6 種排法(右上/右下板長沿 X 沒有副支頂它)都要被抓到,
# 不多不少;套用時這 14 種都要全綠(由標準答案與掃描驗)。
want14 = ({("F1客廳", fo.layout_name(l)) for l in fo.LAYOUTS}
          | {("F2主臥", fo.layout_name(l)) for l in fo.LAYOUTS if fo.layout_name(l) not in ("右上起鋪,板長沿X", "右下起鋪,板長沿X")})
caught, promoted = set(), 0
for name in ("F1客廳", "F2主臥"):
    for l in fo.LAYOUTS:
        promoted += sum(1 for t in fo.build(R[name], l, p)["timbers"] if t.get("core_role") == "custom" and t["kind"] != "rc_parallel")
        res = fo.build(R[name], l, p, frozenset({"no_custom4"}))
        if "C8_I19_PRIORITY" in {f["check"] for f in fo.check(res, p)}:
            caught.add((name, fo.layout_name(l)))
ok = caught == want14
failed |= not ok
print(f"[{'紅' if ok else '錯!'}] no_custom4         {len(caught)}/{len(want14)} 個排法被 C8_I19_PRIORITY 抓到"
      f"(多抓 {sorted(caught - want14)},漏抓 {sorted(want14 - caught)});套用時升格 custom 4 的副支 {promoted} 支")
for name in ("F1客廳", "F2主臥", "F3次臥", "F5廚房"):
    res = fo.build(R[name], LT_Y, p)
    fails = fo.check(res, p)
    ok = not res["conflicts"] and not fails
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] 對照 {name} 左上 Y")
res = fo.build(STEP20, next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左下起鋪,板長沿X"), p)
fails = fo.check(res, p)
ok = not res["conflicts"] and not fails
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] 對照 20 mm 牆階 左下 X(沿牆料端面頂延伸段,宣告 custom 3){sorted({f['check'] for f in fails})}")
# 牆階:這些排法要可施工、全部檢查通過(短段不放料、FT02 照縫線上最近的對牆挪縫)
for room_, lay_, why_ in (
        (STEP40, "左下起鋪,板長沿Y", "牆階面剩 13 mm 不放料"),
        (STEP20, "左上起鋪,板長沿X", "FT02 照 y=3680 牆挪縫到 3639,主支貼住 x>2600 的牆料"),
        (STEP40, "左上起鋪,板長沿X", "FT02 挪縫到 3619"),
        (STEP40, "左上起鋪,板長沿Y", "板端縫 FT02 挪到 3619"),
        (STEP45, "左上起鋪,板長沿Y", "板端縫退到 y=3655 牆的 G7 位置 3614,承接帶不落在牆階短段")):
    res = fo.build(room_, next(l for l in fo.LAYOUTS if fo.layout_name(l) == lay_), p)
    fails = fo.check(res, p)
    ok = not res["conflicts"] and not fails
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] 對照 {3700 - room_['outer'][2][1]} mm 牆階 {lay_}:可施工({why_})"
          f"{sorted({c['code'] for c in res['conflicts']})}{sorted({f['check'] for f in fails})}")
# 平移退回置中仍要有效:照舊縫位(bbox_ft02,縫 3659)時,40 mm 牆階的主支被推去撞 y=3700 的牆料就要退回置中,
#   原因要是核心限制(主支頂延伸段),不是碰撞
res = fo.build(STEP40, next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左上起鋪,板長沿X"), p, frozenset({"bbox_ft02"}))
got_ = sorted({c["code"] for c in res["conflicts"]})
ok = got_ == ["CORE_LIMIT_MAIN_ON_EXTENSION"]
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] 對照 40 mm 牆階 左上 X、照舊縫位:平移撞牆料時退回置中,原因要是核心限制 {got_}")
# 牆階掃描裡仍判不可施工的兩類(都是核心限制),各挑一個,原因代碼要完全一致(理由寫在 README 的核心限制清單)
for room_, lay_, want_, why_ in (
        (STEP45, "左上起鋪,板長沿X", ["CORE_LIMIT_MAIN_ON_EXTENSION"], "核心限制(主支頂延伸段),不是碰撞"),
        (STEP20, "左上起鋪,板長沿Y", ["CORE_LIMIT_BOUNDARY_END_FREE", "SPAN_END_NOT_ON_BOUNDARY"], "核心限制(邊界材端面懸空,延伸會撞另一支牆邊界材)")):
    res = fo.build(room_, next(l for l in fo.LAYOUTS if fo.layout_name(l) == lay_), p)
    got_ = sorted({c["code"] for c in res["conflicts"]})
    ok = got_ == want_
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] 對照 {3700 - room_['outer'][2][1]} mm 牆階 {lay_}:不可施工,原因要是{why_} {got_}")
# 剛好 min_piece 的料必須放(建構端兩處邊界:跨寬、柱面料切段),而且全部檢查通過
res = fo.build(T27, LT_Y, p)
fails = fo.check(res, p)
ln = lambda t: fo.rng(t["rect"], res["a"])[1] - fo.rng(t["rect"], res["a"])[0]
sec27 = [t for t in res["timbers"] if t["kind"] == "secondary" and ln(t) == p["min_piece"]]
col27 = [t for t in res["timbers"] if t["kind"] == "boundary" and not t["outer"] and ln(t) == p["min_piece"]]
ok = not res["conflicts"] and not fails and len(sec27) > 0 and len(col27) == 2
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] 剛好 {p['min_piece']} mm 要放:副支 {len(sec27)} 支、柱面料 {len(col27)} 支(要 2),"
      f"衝突 {sorted({c['code'] for c in res['conflicts']})},檢查失敗 {sorted({f['check'] for f in fails})}")
# 副支 custom 4 的兩個條件(合成案例,直接呼叫 promote_custom4;A 軸 = x、B 軸 = y):
#   柱面料(boundary、不貼外牆)端面頂 custom 3 → 升格;寬向沒有被 custom 料蓋住的副支,端面座標再巧合也不升格;
#   外牆 boundary、主支不升格。拿掉柱面料分支或寬向條件都要轉紅。
cust = dict(kind="rc_parallel", rect=(100, 0, 127, 1000), core_role="custom", priority=3)
cases = dict(
    col=dict(kind="boundary", rect=(127, 500, 400, 527), outer=False),
    sec=dict(kind="secondary", rect=(127, 700, 600, 727), role="mark"),
    sec_far=dict(kind="secondary", rect=(127, 1200, 600, 1227), role="mark"),
    sec_part=dict(kind="secondary", rect=(127, 990, 600, 1017), role="mark"),
    outer=dict(kind="boundary", rect=(127, 0, 600, 27), outer=True),
    main=dict(kind="main", rect=(127, 0, 154, 1000)),
)
fo.promote_custom4([cust] + list(cases.values()), 0, 1)
got = {k for k, t in cases.items() if t.get("core_role") == "custom" and t.get("priority") == 4}
ok = got == {"col", "sec"}
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] custom 4 合成案例:升格 {sorted(got)}(要 ['col', 'sec'];柱面料分支與寬向條件都有走到)")

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
if MUTANTS_ONLY:
    print("(--mutants-only:跳過掃描)")
    sys.exit(1 if failed else 0)

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
# 凹角房:L 形(缺一角)與壁龕(牆上內凹),8 種排法;可施工的排法都要通過全部檢查(含 C8 核心可表示)
LROOM = lambda W, H, cw, ch: {"outer": [[0, 0], [W, 0], [W, H - ch], [W - cw, H - ch], [W - cw, H], [0, H]]}
ALCOVE = lambda W, H, y0, y1, dep: {"outer": [[dep, 0], [W, 0], [W, H], [dep, H], [dep, y1], [0, y1], [0, y0], [dep, y0]]}
reflex_rooms = [LROOM(W, H, cw, ch) for W in (3000, 4100, 5000) for H in (2600, 3700, 4800)
                for cw in range(300, W - 299, 457) for ch in range(300, H - 299, 613)]
reflex_rooms += [ALCOVE(W, 3000, y0, y0 + L, dep) for W in (3000, 4400) for y0 in (400, 1000, 1700)
                 for L in (400, 900) for dep in (300, 600) if y0 + L <= 2600]
COLUMN = lambda W, H, x, y, cs: {"outer": [[0, 0], [W, 0], [W, H], [0, H]], "holes": [[[x, y], [x + cs, y], [x + cs, y + cs], [x, y + cs]]]}
reflex_rooms += [COLUMN(W, H, x, y, cs) for W, H in ((3600, 3000), (5000, 4200)) for cs in (300, 450)
                 for x in range(500, W - cs - 499, 433) for y in range(500, H - cs - 499, 521)]
rb, rbuild = [], 0
codes = {}
for room in reflex_rooms:
    for l in fo.LAYOUTS:
        runs += 1
        res = fo.build(room, l, p)
        if res["conflicts"]:
            for c in res["conflicts"]:
                codes[c["code"]] = codes.get(c["code"], 0) + 1
            continue
        rbuild += 1
        fails = fo.check(res, p)
        if fails:
            rb.append((room["outer"], fo.layout_name(l), sorted({f["check"] for f in fails})))
# 牆階 1–100 mm:L 形缺角很淺(橫向或縱向)與很淺的壁龕,8 種排法。可施工的排法都要通過全部檢查。
#   (#251 審查 60785906:牆階 13–24 mm 時沿牆料端面頂延伸段,原本沒宣告 custom 3,C8_I19_PRIORITY 會紅。)
step_rooms = ([LROOM(4100, 3700, 1500, s) for s in range(1, 101)] + [LROOM(4100, 3700, s, 1200) for s in range(1, 101)]
              + [ALCOVE(4100, 3000, 1000, 1900, s) for s in range(1, 101)])
sbuild, sbad, scodes = 0, 0, {}
for room in step_rooms:
    for l in fo.LAYOUTS:
        runs += 1
        res = fo.build(room, l, p)
        if res["conflicts"]:
            for c in {c["code"] for c in res["conflicts"]}:
                scodes[c] = scodes.get(c, 0) + 1
            continue
        sbuild += 1
        fails = fo.check(res, p)
        if fails:
            sbad += 1
            rb.append((room["outer"], fo.layout_name(l), sorted({f["check"] for f in fails})))
print(f"牆階 1–100 mm 的 L 形與壁龕 {len(step_rooms)} 間 × 8 種排法:可施工 {sbuild} 個,其中檢查失敗 {sbad} 個;"
      f"不可施工的排法數(依原因){scodes}")
# 奇數縫寬:縫寬 1、3 的矩形房,8 種排法(反向起鋪首縫取上界)
p_odd = [dict(p, gap=gg) for gg in (1, 3)]
odd_bad = odd_runs = 0
for pp in p_odd:
    for W in range(1200, 4001, 233):
        for H in range(1900, 5001, 377):
            for l in fo.LAYOUTS:
                odd_runs += 1
                res = fo.build(RECT(W, H), l, pp)
                fl = [] if res["conflicts"] else fo.check(res, pp)
                if res["conflicts"] or fl:
                    odd_bad += 1
                    rb.append(((W, H, pp["gap"]), fo.layout_name(l), sorted({c["code"] for c in res["conflicts"]} | {f["check"] for f in fl})))
print(f"奇數縫寬(1、3)矩形房 {odd_runs} 次:不可施工或檢查失敗 {odd_bad} 個")
print(f"凹角、壁龕與獨立柱房 {len(reflex_rooms)} 間 × 8 種排法:可施工 {rbuild} 個,其中檢查失敗 {len(rb)} 個;不可施工的原因 {codes}")
for x in rb[:10]:
    print("   ", x)
bad += rb
print(f"掃描 {runs} 次矩形房建構({'完整' if FULL else '快速'}),{time.time() - t0:.0f} 秒;不可施工或檢查失敗 {len(bad)} 個")
for b in bad[:30]:
    print("   ", b)
failed |= bool(bad)
sys.exit(1 if failed else 0)
