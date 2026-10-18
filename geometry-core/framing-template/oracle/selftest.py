"""framing_oracle 的自我測試。
(1) 突變:拿掉或弄偏某條規則,對應的檢查必須轉紅;未突變的對照組必須全綠。
    另跑 no_custom4(不套副支 custom 4):F1、F2 那 14 種排法都要被 C8_I19_PRIORITY 抓到,不多不少。
    剛好 min_piece(27 mm)的副支與柱面料必須放(T27 房);custom 4 的柱面料分支與寬向條件用合成案例驗。
(3c) 牆階 1–100 mm 的 L 形與壁龕 300 間、雙牆階 110 間,各 8 種排法,可施工的排法都要通過全部檢查。
用法另有 --mutants-only:只跑 (1)(2),跳過掃描。(1) 也包括引文逐字檢查(quote_check.py,讀 origin/main 的 決策佇列.md)
    與掃描斷言比對函式 compare_unbuildable 的直接測試。
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
# 記號合成格長:深 3301,左上起鋪板長沿 Y,板端縫 1831,第二格 1831–3301 長 1470 = 367×4 + 2,餘數 2 mm,最後一支會碰到牆邊界材
JIG1470 = RECT(2000, 3301)
# 板端縫端餘數 < 27 的合成格:板長改 1468(縫距 1470),板端縫 1469、2939、4409;縫到縫那一格 1470 = 367×4 + 2,最後一支會碰到下一條縫的縫上副支
JIGSEAM = dict(RECT(2000, 4500), params={"L": 1468})
# P-180:柱面料 [1816,1843] 蓋住板端縫 1831,比置中的縫上副支短 2 mm;這一跨的縫上副支要貼著柱面料放在 [1843,1870]
COLUMN = lambda W, H, x, y, cs: {"outer": [[0, 0], [W, 0], [W, H], [0, H]], "holes": [[[x, y], [x + cs, y], [x + cs, y + cs], [x, y + cs]]]}
COL2MM = COLUMN(3600, 3000, 1366, 500, 450)
LROOM = lambda W, H, cw, ch: {"outer": [[0, 0], [W, 0], [W, H - ch], [W - cw, H - ch], [W - cw, H], [0, H]]}
# P-180 的 L 形版:外牆凹角面 y=1846 落在板端縫 1831 之後 15 mm(審查員 exp7)
L1846 = LROOM(4000, 4500, 1500, 4500 - 1846)
# 40 mm 牆階:牆階面 y 3660–3700 被 y=3700 牆的邊界材蓋掉 27 mm,只剩 13 mm,不放沿牆料
#   (柱面是使用者 10-18 的決定,選項原文「不放(短於 27 一律不放)」;牆面比照是推論)
STEP40 = {"outer": [[0, 0], [4100, 0], [4100, 3660], [2600, 3660], [2600, 3700], [0, 3700]]}
# 45 mm 牆階:牆階牆 y=3655 在縫 3659 前面,縫線不伸進淺的那段,只看縫線的 G7 不挪。
#   板端縫(板長沿 Y)由退縫規則退到 3614;主支縫(板長沿 X)的主支 [3646,3673] 跨過 y=3655,由 P-182 退到 3614
STEP45 = {"outer": [[0, 0], [4100, 0], [4100, 3655], [2600, 3655], [2600, 3700], [0, 3700]]}
# 雙牆階(牆 y=s1 在 x 2600–3300、y=s2 在 x 3300–4100),和掃描裡的 DS:s1,s2 同一族
DSROOM = lambda s1, s2: {"outer": [[0, 0], [4100, 0], [4100, s2], [3300, s2], [3300, s1], [2600, s1], [2600, 3700], [0, 3700]]}
# 30 mm 牆階:牆階面只剩 3 mm,縫 3659 的承接帶碰不到它,不會觸發退縫;只有 G7 照縫線上最近的對牆(y=3670)才會把板端縫挪到 3629
STEP30 = {"outer": [[0, 0], [4100, 0], [4100, 3670], [2600, 3670], [2600, 3700], [0, 3700]]}
# 41 mm 牆階:G7 第一次把縫挪到 3659,剛好落在 y=3659 那面牆的牆線上;那面牆要算在縫前面,再挪到 3618
STEP41 = {"outer": [[0, 0], [4100, 0], [4100, 3659], [2600, 3659], [2600, 3700], [0, 3700]]}
# 雙牆階(#251 審查 98cb7da0 的反例):45 mm 牆階退縫到 3614 後,縫線伸進 x>3300 那段,那裡的對牆在 3628,只剩 13 mm;G7 要再挪到 3587
DSTEP = {"outer": [[0, 0], [4100, 0], [4100, 3628], [3300, 3628], [3300, 3655], [2600, 3655], [2600, 3700], [0, 3700]]}

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
    ("no_fill", R["F2主臥"], "C4_SPACING", "記號撞到壁柱邊界材拿掉後,不在旁邊補一支:間距超過上限", "左上起鋪,板長沿Y"),
    ("shift_mark_rects", R["F3次臥"], "C12_MARK_OFF_JIG", "記號副支的矩形整排移 -8 mm、at 標籤不動:C12 要看實際位置"),
    ("fill_relabel", R["F2主臥"], "C13_EXTRA_OFF_RULE", "把一支記號移 -8 mm 後改標 fill:fill 沒有貼著擋料", "左上起鋪,板長沿Y"),
    ("fill_extra", R["F2主臥"], "C13_EXTRA_UNNEEDED", "在兩支記號中間憑空多放一支 fill:拿掉它間距也不超上限", "左上起鋪,板長沿Y"),
    ("fill_double", R["F2主臥"], "C13_EXTRA_DOUBLED", "fill 改成貼著旁邊那支記號:雙拼", "左上起鋪,板長沿Y"),
    ("no_seam_window", R["F1客廳"], "C4_SPACING", "縫上副支的範圍不受「與鄰近記號的間距上限」約束:為了對齊挪到 3151,與記號 3536 空檔 345", "右上起鋪,板長沿X"),
    ("extra_seam_mid", R["F3次臥"], "C13_EXTRA_OFF_RULE", "兩支記號正中間多放一支、標成 seam:不在縫上、不貼擋料"),
    ("extra_norole_mid", R["F3次臥"], "C13_EXTRA_OFF_RULE", "同上,但不給 role"),
    ("seam_relabel", R["F3次臥"], "C12_JIG_MARK_MISSING", "把一支記號移 -8 mm 後改標 seam:治具位置空了,改標的那支不算合法擋料"),
    ("no_seam_at_end", COL2MM, "C4_SPACING", "P-180 拿掉:柱面料蓋住縫時不放縫上副支,空檔 342", "左上起鋪,板長沿X"),
    ("no_merge_seam_end", JIGSEAM, "C12_JIG_MARK_MISSING", "板端縫端不合併平分:1470 那格最後一支碰到下一條縫的縫上副支,掉了"),
    ("even_split", R["F3次臥"], "C12_MARK_OFF_JIG", "記號退回逐格均分(舊公式 m=⌈L/n⌉):F3 最後一格 1449 mm 用 363,不是同一治具 367"),
    ("no_merge_split", JIG1470, "C12_JIG_MARK_MISSING", "拿掉「最後一支記號碰到格端就合併平分」:1470 mm 那格的最後一支掉了,3117 沒有記號"),
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
    ("short_face_conflict", STEP40, "C10_SHORT_PIECE", "牆階 40 mm:牆階面只剩 13 mm 也放沿牆料(不照短於 27 不放的規則;牆面比照柱面是推論)", "左下起鋪,板長沿Y"),
    ("bbox_ft02", STEP20, "C7_SEAMS_NOT_FROM_START", "FT02 退回照外框挪縫(3659):縫線上最近的對牆是 x>2600 的 y=3680 牆,應挪到 3639", "左上起鋪,板長沿X"),
    ("bbox_ft02", STEP30, "C7_SEAMS_NOT_FROM_START", "同上,板端縫(B 軸):30 mm 牆階應挪到 3629(40 mm 牆階時退縫規則也會退到同一處,抓不出差別,所以換這間)", "左上起鋪,板長沿Y"),
    ("bbox_ft02+no_push_fallback", STEP40, "C1_OVERLAP", "照外框挪縫時,讓開牆料的平移撞到 y=3700 的牆料,沒有退回置中", "左上起鋪,板長沿X"),
    ("no_seam_retreat", STEP45, "C7_SEAMS_NOT_FROM_START", "45 mm 牆階:板端縫 3659 的承接帶落在牆階面沒料的 18 mm 裡,沒有往內退到 3614", "左上起鋪,板長沿Y"),
    ("no_resettle", DSTEP, "C7_SEAMS_NOT_FROM_START", "雙牆階:退縫到 3614 後沒有再跑 G7,x>3300 那段只剩 13 mm 的收邊板條(應挪到 3587)", "左上起鋪,板長沿Y"),
    ("no_main_band_depth", STEP45, "C7_SEAMS_NOT_FROM_START", "拿掉 P-182:主支縫只看縫線,y=3655 那面牆落在最後一支主支 [3646,3673] 的寬度裡,沒有退到 3614", "左上起鋪,板長沿X"),
    ("no_main_band_depth", STEP45, "C7_G7_TOO_CLOSE", "同上,C7b 直接驗結果:主支起鋪側側面那條線上的對牆 y=3655 離縫 3659 不到 1.5w", "左上起鋪,板長沿X"),
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
for room_, tag_, lay_, why_, want_seam in (
        (STEP40, "40 mm 牆階", "左下起鋪,板長沿Y", "牆階面剩 13 mm 不放料", None),
        (STEP20, "20 mm 牆階", "左上起鋪,板長沿X", "G7 照 y=3680 牆挪縫,主支貼住 x>2600 的牆料", ("a", 3639)),
        (STEP40, "40 mm 牆階", "左上起鋪,板長沿X", "G7 挪縫", ("a", 3619)),
        (STEP40, "40 mm 牆階", "左上起鋪,板長沿Y", "板端縫 G7 挪縫", ("b", 3619)),
        (STEP45, "45 mm 牆階", "左上起鋪,板長沿Y", "板端縫退到 y=3655 牆的 G7 位置,承接帶不落在牆階短段", ("b", 3614)),
        (STEP41, "41 mm 牆階", "左上起鋪,板長沿X", "縫挪到 3659 時剛好落在牆線上,那面牆算在縫前面,再挪", ("a", 3618)),
        (STEP30, "30 mm 牆階", "左上起鋪,板長沿Y", "板端縫 G7 照 y=3670 牆挪縫", ("b", 3629)),
        (DSTEP, "雙牆階", "左上起鋪,板長沿Y", "板端縫先退到 3614,縫線伸進 x>3300 那段(對牆 3628),G7 再挪", ("b", 3587)),
        # P-182(推論):主支縫的對牆看主支整條寬度。審查員舉的例子與一個先由縫線 G7 挪、再由主支寬度退的例子
        (STEP45, "45 mm 牆階", "左上起鋪,板長沿X", "P-182:y=3655 牆落在主支寬度裡,主支縫退到 ⌊3655 − 40.5⌋", ("a", 3614)),
        (LROOM(4100, 3700, 1500, 54), "54 mm 牆階", "左上起鋪,板長沿X", "y=3646 剛好貼著主支起鋪側側面 [3646,3673],不算擋到主支,不退", ("a", 3659)),
        (LROOM(4100, 3700, 1500, 53), "53 mm 牆階", "右上起鋪,板長沿X", "P-182:主支縫退到 ⌊3647 − 40.5⌋", ("a", 3606)),
        (DSROOM(3649, 3597), "雙牆階 3649/3597", "左上起鋪,板長沿X", "P-182:先退到 3608,主支 [3595,3622] 又跨過 y=3597,G7 再退到 3556", ("a", 3556)),
        (DSROOM(3658, 3570), "雙牆階 3658/3570", "右上起鋪,板長沿X", "P-182:退到 3617,主支 [3604,3631] 不碰 y=3570,停在離原位最近的位置", ("a", 3617)),
        (DSROOM(3667, 3615), "雙牆階 3667/3615", "左上起鋪,板長沿X", "縫線 G7 先照 y=3667 挪到 3626,主支 [3613,3640] 跨過 y=3615,P-182 再退到 3574", ("a", 3574))):
    res = fo.build(room_, next(l for l in fo.LAYOUTS if fo.layout_name(l) == lay_), p)
    fails = fo.check(res, p)
    got_seam = None if want_seam is None else res["seams_" + want_seam[0]][-1]
    ok = not res["conflicts"] and not fails and (want_seam is None or got_seam == want_seam[1])
    failed |= not ok
    seam_txt = "" if want_seam is None else f",最後一條{'板端縫' if want_seam[0] == 'b' else '縫'}要在 {want_seam[1]}(實得 {got_seam})"
    print(f"[{'綠' if ok else '錯!'}] 對照 {tag_} {lay_}:可施工({why_}{seam_txt})"
          f"{sorted({c['code'] for c in res['conflicts']})}{sorted({f['check'] for f in fails})}")
# C7b 專屬:把雙牆階的最後一條板端縫改回 3614(x>3300 那段只剩 13 mm),C7_G7_TOO_CLOSE 要報。只拿掉 C7b 時這一行轉紅。
res = fo.build(DSTEP, next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左上起鋪,板長沿Y"), p)
res["seams_b"] = res["seams_b"][:-1] + [3614]
got_ = {f["check"] for f in fo.check(res, p)}
ok = "C7_G7_TOO_CLOSE" in got_
failed |= not ok
print(f"[{'紅' if ok else '沒抓到!'}] tamper_seam        預期 C7_G7_TOO_CLOSE          實得 {sorted(got_)}  雙牆階的板端縫改回 3614:離 x>3300 的對牆只剩 13 mm")
# C7b 的主支寬度那一半(P-182):把 45 mm 牆階左上 X 的最後一條主支縫改回 3659,主支 [3646,3673] 跨過 y=3655,C7_G7_TOO_CLOSE 要報
res = fo.build(STEP45, next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左上起鋪,板長沿X"), p)
res["seams_a"] = res["seams_a"][:-1] + [3659]
got_ = {f["check"] for f in fo.check(res, p)}
ok = "C7_G7_TOO_CLOSE" in got_
failed |= not ok
print(f"[{'紅' if ok else '沒抓到!'}] tamper_main_seam   預期 C7_G7_TOO_CLOSE          實得 {sorted(got_)}  45 mm 牆階的主支縫改回 3659:主支寬度跨過 y=3655 那面牆")
# C13 的「那支治具記號確實放不下」:F2 右上 X 有一支記號 [8624,8651] 離上面的邊界材 [8673,8700] 只差 22 mm、本來放得下;
#   把它換成一支貼著邊界材的 fill [8646,8673],離治具位置 < w、也貼著擋料,只有這一條能判它不合規則。
res = fo.build(R["F2主臥"], next(l for l in fo.LAYOUTS if fo.layout_name(l) == "右上起鋪,板長沿X"), p)
tgt = [t for t in res["timbers"] if t.get("role") == "mark" and tuple(t["rect"]) == (8624, 930, 8651, 1820)]
if tgt:
    tgt[0]["rect"], tgt[0]["role"] = (8646, 930, 8673, 1820), "fill"
got_ = {f["check"] for f in fo.check(res, p)}
ok = bool(tgt) and "C13_EXTRA_OFF_RULE" in got_
failed |= not ok
print(f"[{'紅' if ok else '沒抓到!'}] tamper_fill_plausible 預期 C13_EXTRA_OFF_RULE   實得 {sorted(got_)}  F2 右上 X 把放得下的記號換成貼邊界材的 fill")
# 平移退回置中仍要有效:照舊縫位(bbox_ft02,縫 3659)時,40 mm 牆階的主支被推去撞 y=3700 的牆料就要退回置中,
#   原因要是核心限制(主支頂延伸段),不是碰撞
res = fo.build(STEP40, next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左上起鋪,板長沿X"), p, frozenset({"bbox_ft02"}))
got_ = sorted({c["code"] for c in res["conflicts"]})
ok = got_ == ["CORE_LIMIT_MAIN_ON_EXTENSION"]
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] 對照 40 mm 牆階 左上 X、照舊縫位:平移撞牆料時退回置中,原因要是核心限制 {got_}")
# 退縫做不到時要報衝突、寫明理由,不能默默排出板邊沒料的排法:關掉退縫,45 mm 牆階左上 Y 要報 SHORT_FACE_SEAM_EDGE_UNSUPPORTED
res = fo.build(STEP45, next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左上起鋪,板長沿Y"), p, frozenset({"no_seam_retreat"}))
got_ = sorted({c["code"] for c in res["conflicts"]})
ok = got_ == ["SHORT_FACE_SEAM_EDGE_UNSUPPORTED"]
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] 對照 45 mm 牆階 左上 Y、不退縫:板端縫承接帶落在牆階短段要報衝突 {got_}")
# 牆階掃描裡仍判不可施工的那一類(核心限制),挑一個,原因代碼要完全一致(理由寫在 README 的核心限制清單)。
#   原本的另一類(主支頂延伸段,80 個排法)由 P-182 解開,見上面的對照與突變 no_main_band_depth;那條核心限制的判定仍由
#   「照舊縫位時平移撞牆料要退回置中」那個對照留著牙齒。
for room_, lay_, want_, why_ in (
        (STEP20, "左上起鋪,板長沿Y", ["CORE_LIMIT_BOUNDARY_END_FREE", "SPAN_END_NOT_ON_BOUNDARY"], "核心限制(邊界材端面懸空,延伸會撞另一支牆邊界材)"),):
    res = fo.build(room_, next(l for l in fo.LAYOUTS if fo.layout_name(l) == lay_), p)
    got_ = sorted({c["code"] for c in res["conflicts"]})
    ok = got_ == want_
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] 對照 {3700 - room_['outer'][2][1]} mm 牆階 {lay_}:不可施工,原因要是{why_} {got_}")
# 記號同一治具 367(使用者 2026-10-18 拍板「乙 同一治具 367」):完整格要和以前一樣(367×4+363/364);1470 mm 的格最後兩步合併平分
for room_, tag_, cell_, want_ in (
        (R["F3次臥"], "F3 第一格 1831(牆到板端縫)", (3720, 5551), [4083, 4450, 4817, 5184]),
        (R["F1客廳"], "F1 第一格 1831", (0, 1831), [363, 730, 1097, 1464]),
        (R["F1客廳"], "F1 第二格 1832(板端縫到板端縫)", (1831, 3663), [2198, 2565, 2932, 3299]),
        (JIG1470, "合成格 1470(牆端,餘數 2)", (1831, 3301), [2198, 2565, 2932, 3117]),
        (JIGSEAM, "合成格 1470(板端縫端,餘數 2)", (1469, 2939), [1836, 2203, 2570, 2755])):
    pp_ = dict(p, **room_.get("params", {}))
    res = fo.build(room_, LT_Y, pp_)
    got_ = sorted({t["at"] for t in res["timbers"] if t.get("role") == "mark" and cell_[0] < t["at"] < cell_[1]})
    ok = got_ == want_ and not res["conflicts"] and not fo.check(res, pp_)
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] 記號 {tag_} 左上 Y:要 {want_},實得 {got_}")
# 縫上副支平移不再觸發補位:F1 右上 X 的板端縫 3169,貼內牆那幾跨被逼到 3146,其他跨要在 3156(與記號 3536、2802 各空 340),整個排法沒有 fill
res = fo.build(R["F1客廳"], next(l for l in fo.LAYOUTS if fo.layout_name(l) == "右上起鋪,板長沿X"), p)
seam_lo = sorted({fo.rng(t["rect"], res["b"])[0] for t in res["timbers"] if t.get("role") == "seam" and t.get("at") == 3169})
nfill = sum(1 for t in res["timbers"] if t.get("role") == "fill")
ok = seam_lo == [3146, 3156] and nfill == 0 and not res["conflicts"] and not fo.check(res, p)
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] 縫上副支受間距上限約束:F1 右上 X 板端縫 3169 的副支起點 {seam_lo}(要 [3146, 3156]),fill {nfill} 支(要 0)")
# P-180:柱面料或外牆凹角面蓋住板端縫、少了縫上副支下一格空檔會超上限時,縫上副支貼著擋料放(不是 fill)
for room_, lay_, want_ in ((COL2MM, "左上起鋪,板長沿X", [1818, 1843]), (L1846, "左上起鋪,板長沿Y", None)):
    res = fo.build(room_, next(l for l in fo.LAYOUTS if fo.layout_name(l) == lay_), p)
    seam_lo = sorted({fo.rng(t["rect"], res["b"])[0] for t in res["timbers"] if t.get("role") == "seam" and t.get("at") == 1831})
    nfill = sum(1 for t in res["timbers"] if t.get("role") == "fill")
    ok = not res["conflicts"] and not fo.check(res, p) and nfill == 0 and (want_ is None or seam_lo == want_)
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] P-180 {room_['outer'][2]} {lay_}:可施工,縫 1831 的縫上副支起點 {seam_lo}"
          f"{'(要 ' + str(want_) + ')' if want_ else ''},fill {nfill} 支")
# 掃描斷言的牙齒(#251 審查 178ba084 第 6 項):掃描的比對寫成函式 compare_unbuildable,下面直接測它,--mutants-only 也會走到。
#   (a) 合成:預期清單拿掉一筆、改掉一筆的原因代碼,函式要逐筆指出(多出/少了);(b) 拿掉 P-180,柱房那幾個原本可施工的排法
#   退化成 MARK_NO_ROOM,和預期清單比對要不一致;(c) 照原樣建構,比對要一致。


def compare_unbuildable(got, want):
    """掃描斷言:實得的不可施工集合與預期清單逐筆比對(排法 id、排法、原因代碼都要一樣),回傳 (多出, 少了),兩個都空才算一致。"""
    got, want = set(got), set(want)
    return sorted(got - want), sorted(want - got)


EXP_PATH = HERE / "sweep-expected-unbuildable.json"
_mini = [(f"C:3600,3000,1366,{y},450", COLUMN(3600, 3000, 1366, y, 450)) for y in (500, 1021, 1542)]
_exp_all = json.load(open(EXP_PATH, encoding="utf-8")) if EXP_PATH.exists() else {"reflex": [], "step": []}
_exp_mini = {(r_, l_, tuple(c_)) for r_, l_, c_ in _exp_all["reflex"] if any(r_ == i_ for i_, _ in _mini)}
_syn = [("L_ch:1", "左上起鋪,板長沿Y", ("CORE_LIMIT_BOUNDARY_END_FREE", "SPAN_END_NOT_ON_BOUNDARY")),
        ("L_ch:2", "左上起鋪,板長沿Y", ("CORE_LIMIT_BOUNDARY_END_FREE", "SPAN_END_NOT_ON_BOUNDARY")),
        ("L_cw:3", "左下起鋪,板長沿X", ("CORE_LIMIT_BOUNDARY_END_FREE", "SPAN_END_NOT_ON_BOUNDARY"))]
_syn_got = _syn[:1] + [(_syn[1][0], _syn[1][1], ("CORE_LIMIT_BOUNDARY_END_FREE",))]
_x, _m = compare_unbuildable(_syn_got, _syn)
ok = _x == [_syn_got[1]] and _m == sorted([_syn[1], _syn[2]])
failed |= not ok
print(f"[{'紅' if ok else '沒抓到!'}] compare_unbuildable 合成:預期 3 筆、實得少一筆又改掉一筆的原因代碼;多出 {_x},少了 {_m}")


def _unbuildable(rooms_, mut_=frozenset()):
    out_ = set()
    for rid_, room_ in rooms_:
        pp_ = dict(p, **room_.get("params", {}))
        for l_ in fo.LAYOUTS:
            r_ = fo.build(room_, l_, pp_, mut_)
            if r_["conflicts"]:
                out_.add((rid_, fo.layout_name(l_), tuple(sorted({c["code"] for c in r_["conflicts"]}))))
    return out_


_x0, _m0 = compare_unbuildable(_unbuildable(_mini), _exp_mini)
_x1, _m1 = compare_unbuildable(_unbuildable(_mini, frozenset({"no_seam_at_end"})), _exp_mini)
ok = not _x0 and not _m0 and bool(_x1 or _m1)
failed |= not ok
print(f"[{'紅' if ok else '沒抓到!'}] sweep_assert       預期 不可施工清單不一致  拿掉 P-180 時柱房退化成 MARK_NO_ROOM:"
      f"多出 {len(_x1)} 筆(第一筆 {(_x1 or [None])[0]}),少了 {len(_m1)} 筆;照原樣建構時多出 {len(_x0)}、少了 {len(_m0)}")
# 引文逐字(#251 審查 178ba084 第 2、3 項):標成使用者原話的引文都要逐字出現在 origin/main 的 決策佇列.md;反例要抓到、正例要過
sys.path.insert(0, str(HERE))
import quote_check  # noqa: E402

try:
    _queue = quote_check.queue_from_origin_main()
except Exception as e_:  # 沒有 origin/main(例:淺層 clone)就算失敗,不默默略過
    _queue = None
    failed = True
    print(f"[錯!] 引文逐字:讀不到 origin/main 的 決策佇列.md({e_.__class__.__name__});先 git fetch origin main")
if _queue is not None:
    _nq, _badq = quote_check.scan(_queue)
    _wrongq = quote_check.self_check(_queue)
    ok = not _badq and not _wrongq
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] 引文逐字({quote_check.queue_source()}):標成原話的引文 {_nq} 段都逐字出現在 決策佇列.md(不一致 {len(_badq)});"
          f"反例 {sum(1 for _, b in quote_check.SAMPLES if b)} 個都抓到、正例 {sum(1 for _, b in quote_check.SAMPLES if not b)} 個都過(判錯 {len(_wrongq)})")
    for x in _badq + _wrongq:
        print("    ", x)
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
reflex_rooms = [(f"L:{W},{H},{cw},{ch}", LROOM(W, H, cw, ch)) for W in (3000, 4100, 5000) for H in (2600, 3700, 4800)
                for cw in range(300, W - 299, 457) for ch in range(300, H - 299, 613)]
reflex_rooms += [(f"A:{W},{y0},{L},{dep}", ALCOVE(W, 3000, y0, y0 + L, dep)) for W in (3000, 4400) for y0 in (400, 1000, 1700)
                 for L in (400, 900) for dep in (300, 600) if y0 + L <= 2600]
reflex_rooms += [(f"C:{W},{H},{x},{y},{cs}", COLUMN(W, H, x, y, cs)) for W, H in ((3600, 3000), (5000, 4200)) for cs in (300, 450)
                 for x in range(500, W - cs - 499, 433) for y in range(500, H - cs - 499, 521)]
rb, rbuild = [], 0
codes = {}
unb = {"reflex": set(), "step": set()}
for rid, room in reflex_rooms:
    for l in fo.LAYOUTS:
        runs += 1
        res = fo.build(room, l, p)
        if res["conflicts"]:
            for c in res["conflicts"]:
                codes[c["code"]] = codes.get(c["code"], 0) + 1
            unb["reflex"].add((rid, fo.layout_name(l), tuple(sorted({c["code"] for c in res["conflicts"]}))))
            continue
        rbuild += 1
        fails = fo.check(res, p)
        if fails:
            rb.append((room["outer"], fo.layout_name(l), sorted({f["check"] for f in fails})))
# 牆階 1–100 mm:L 形缺角很淺(橫向或縱向)與很淺的壁龕,8 種排法。可施工的排法都要通過全部檢查。
#   (#251 審查 60785906:牆階 13–24 mm 時沿牆料端面頂延伸段,原本沒宣告 custom 3,C8_I19_PRIORITY 會紅。)
step_rooms = ([(f"L_ch:{s}", LROOM(4100, 3700, 1500, s)) for s in range(1, 101)] + [(f"L_cw:{s}", LROOM(4100, 3700, s, 1200)) for s in range(1, 101)]
              + [(f"alcove:{s}", ALCOVE(4100, 3000, 1000, 1900, s)) for s in range(1, 101)]
              # 雙牆階(#251 審查 98cb7da0):牆 y=s1(x 2600–3300)、y=s2(x 3300–4100),s2 < s1
              + [(f"DS:{s1},{s2}", {"outer": [[0, 0], [4100, 0], [4100, s2], [3300, s2], [3300, s1], [2600, s1], [2600, 3700], [0, 3700]]})
                 for s1 in range(3604, 3700, 9) for s2 in range(s1 - 88, s1, 9)])
sbuild, sbad, scodes = 0, 0, {}
for rid, room in step_rooms:
    for l in fo.LAYOUTS:
        runs += 1
        res = fo.build(room, l, p)
        if res["conflicts"]:
            for c in {c["code"] for c in res["conflicts"]}:
                scodes[c] = scodes.get(c, 0) + 1
            unb["step"].add((rid, fo.layout_name(l), tuple(sorted({c["code"] for c in res["conflicts"]}))))
            continue
        sbuild += 1
        fails = fo.check(res, p)
        if fails:
            sbad += 1
            rb.append((room["outer"], fo.layout_name(l), sorted({f["check"] for f in fails})))
print(f"牆階 1–100 mm 的 L 形、壁龕與雙牆階 {len(step_rooms)} 間 × 8 種排法:可施工 {sbuild} 個,其中檢查失敗 {sbad} 個;"
      f"不可施工的排法數(依原因){scodes}")
# 不可施工的排法要和明列的預期清單(每筆附原因代碼)完全一樣;清單空的就要 0 個。--write-expected 只在人工覆核後重寫清單。
if "--write-expected" in sys.argv:
    json.dump({fam: sorted([list(x[:2]) + [list(x[2])] for x in v]) for fam, v in unb.items()}, open(EXP_PATH, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=0)
expected_unb = json.load(open(EXP_PATH, encoding="utf-8"))
for fam in ("reflex", "step"):
    want_ = {(r_, l_, tuple(c_)) for r_, l_, c_ in expected_unb[fam]}
    extra_, missing_ = compare_unbuildable(unb[fam], want_)
    ok = not extra_ and not missing_
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] {fam} 掃描的不可施工清單:實得 {len(unb[fam])} 個,預期 {len(want_)} 個;多出 {len(extra_)}、少了 {len(missing_)}")
    for x in extra_[:10]:
        print("     多出", x)
    for x in missing_[:10]:
        print("     少了", x)
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
