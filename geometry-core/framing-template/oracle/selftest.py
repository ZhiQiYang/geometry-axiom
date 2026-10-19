"""framing_oracle 的自我測試。
(1) 突變:拿掉或弄偏某條規則,對應的檢查必須轉紅;未突變的對照組必須全綠。
    另跑 no_custom4(不套副支 custom 4):F1、F2 那 14 種排法都要被 C8_I19_PRIORITY 抓到,不多不少。
    剛好 min_piece(27 mm)的副支與柱面料必須放(T27 房);custom 4 的柱面料分支與寬向條件用合成案例驗。
(3c) 牆階 1–100 mm 的 L 形與壁龕 300 間、雙牆階 110 間,各 8 種排法,可施工的排法都要通過全部檢查。
     同一批房間再上下、左右各翻一次(鏡像),8 種排法:可施工的都要通過全部檢查,不可施工的要等於原房間的清單照鏡像對應
     (左上 ↔ 左下、左上 ↔ 右上),也要等於預期清單的 step_mirror 部分(#251 審查 392d4aa7 阻擋 1)。
用法另有 --mutants-only:只跑 (1)(2),跳過掃描。(1) 也包括引文逐字檢查(quote_check.py,讀受測這棵樹自己的 決策佇列.md)
    與掃描斷言比對函式 compare_unbuildable 的直接測試。
(2) 標準答案:F1–F5 與三個額外例子、8 種排法的輸出,必須與 oracle-golden.json 逐支相同。
(3b) 凹角、壁龕、獨立柱房 579 間與奇數縫寬矩形房,可施工的排法都要通過全部檢查。
(3) 掃描:矩形房。
    快速(預設):2026-10-19 實測時間見 README(和其他程序並行時明顯變慢)。
      - 一維逐 mm:寬 300–4000 × 深 2500,以及寬 2000 × 深 300–6000,只跑左上起鋪、板長沿 Y。
      - 二維 × 8 種排法:寬取 917k+{-43…-39,-1…2}(k=1–4,挪縫臨界帶)與每 331 mm;
        深取 1832k+{-43…-39,-1…2}(k=1–3)與每 617 mm。
    完整(--full):2026-10-19 在 b6856356 實跑 11684 秒(約 3 小時 15 分,nice 10)。
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
# 外框深 3720、x>2600 那段只到 3690:縫線上的對牆是 3690(G7 挪到 3649);照外框則留在 3667,主支推開 18 mm、補併料也排得出
STEP3720 = {"outer": [[0, 0], [4100, 0], [4100, 3690], [2600, 3690], [2600, 3720], [0, 3720]]}
# 雙牆階(牆 y=s1 在 x 2600–3300、y=s2 在 x 3300–4100),和掃描裡的 DS:s1,s2 同一族
DSROOM = lambda s1, s2: {"outer": [[0, 0], [4100, 0], [4100, s2], [3300, s2], [3300, s1], [2600, s1], [2600, 3700], [0, 3700]]}


def MIRROR(room, k):
    """沿軸 k 翻轉房間(k = 1 上下、k = 0 左右),頂點順序反過來;孔一起翻。"""
    o = room["outer"]
    lo_, hi_ = min(q[k] for q in o), max(q[k] for q in o)
    flip = lambda q: [lo_ + hi_ - q[0], q[1]] if k == 0 else [q[0], lo_ + hi_ - q[1]]
    out = dict(room, outer=[flip(q) for q in reversed(o)])
    if room.get("holes"):
        out["holes"] = [[flip(q) for q in reversed(h)] for h in room["holes"]]
    return out


def MIR_LAYOUT(name, k):
    """鏡像房間對應的排法名稱:上下翻轉 上↔下,左右翻轉 左↔右(板長方向不變)。"""
    if k == 1:
        return name[0] + {"上": "下", "下": "上"}[name[1]] + name[2:]
    return {"左": "右", "右": "左"}[name[0]] + name[1:]


# 鏡像的 54 mm 牆階(審查員的反例):置中主支 [28,55] 只跨過 y=54 一 mm(⌊w/2⌋ 與 ⌈w/2⌉ 不對稱),R-butt 平移 1 mm 就不跨,不該退縫
MIR54 = MIRROR(LROOM(4100, 3700, 1500, 54), 1)
# 牆中段的壁柱(左牆 x 0–dx、y y0–y1),和審查員 r15 的 PIL 同一族
PILW = lambda W, H, y0, y1, dx: {"outer": [[0, 0], [W, 0], [W, H], [0, H], [0, y1], [dx, y1], [dx, y0], [0, y0]]}
# 1b6b34f9 審查的兩個退步(P-182 之後要恢復,第三版照樣要對):
#   (1) 牆階 + 柱:主支要讓開 y=3656 那面牆得往上推 2 mm,但會壓到柱下面的柱面料 [3681,3708];舊規則排不出,第二段退到 3615
T9COL = lambda ch: {"outer": [[0, 0], [4100, 0], [4100, 4000 - ch], [2600, 4000 - ch], [2600, 4000], [0, 4000]],
                    "holes": [[[1000, 3708], [1400, 3708], [1400, 3900], [1000, 3900]]]}
#   (2) 左牆中段的壁柱 y 2745–2900:舊規則把主支推開 8 mm、補 3846 mm 併料就排得出,不該退縫多裁一整排板
PIL2745 = PILW(4100, 3200, 2745, 2900, 200)
# P-182 第三版(#251 審查 718cc9a3)的對照房:
#   壁柱 y 2745 加柱 x0–x0+300、y 2650–2850:原縫位沒有衝突碼,但檢查紅(C8 I19、C10),要退縫
PILCOL = lambda x0: dict(PILW(4100, 3200, 2745, 2900, 200), holes=[[[x0, 2650], [x0 + 300, 2650], [x0 + 300, 2850], [x0, 2850]]])
#   45 mm 牆階加柱 x 1000–1400、y 3440–3640:原縫位報 MAIN_HITS_RC_TIMBER(任何衝突碼都要試下一個候選),要退到 3614
S45COL = dict({"outer": [[0, 0], [4100, 0], [4100, 3655], [2600, 3655], [2600, 3700], [0, 3700]]},
              holes=[[[1000, 3440], [1400, 3440], [1400, 3640], [1000, 3640]]])
#   分辨房:x 0–300 的牆 y=3655 是背向起鋪側的牆(室內在它上面),x 3800–4100 的牆 y=3654;兩面都在主支寬度裡
DISTR = {"outer": [[300, 0], [4100, 0], [4100, 3654], [3800, 3654], [3800, 3720], [0, 3720], [0, 3655], [300, 3655]]}
#   三段牆階:兩面牆都在主支寬度裡,近的那個候選(3614)不可行、遠的(3609)可行;由遠到近試會漏掉 3614
TRIPLE = {"outer": [[0, 0], [4100, 0], [4100, 3650], [2600, 3650], [2600, 3655], [1500, 3655], [1500, 3700], [0, 3700]]}
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
    ("bbox_ft02", STEP3720, "C7_SEAMS_NOT_FROM_START", "FT02 退回照外框挪縫:外框深 3720,縫留在 3667;縫線上最近的對牆是 x>2600 的 y=3690 牆,應挪到 3649"
     "(這間的主支推開 18 mm、補併料就排得出,P-182 第二段不會補救;牆階 20–40 mm 那幾間第一段排不出,第二段照主支寬度退到同一處,照外框挪縫的錯在那裡看不出來)", "左上起鋪,板長沿X"),
    ("bbox_ft02", STEP30, "C7_SEAMS_NOT_FROM_START", "同上,板端縫(B 軸):30 mm 牆階應挪到 3629(40 mm 牆階時退縫規則也會退到同一處,抓不出差別,所以換這間)", "左上起鋪,板長沿Y"),
    ("bbox_ft02+no_push_fallback+no_main_band_depth", STEP40, "C1_OVERLAP", "照外框挪縫時,讓開牆料的平移撞到 y=3700 的牆料,沒有退回置中", "左上起鋪,板長沿X"),
    ("no_seam_retreat", STEP45, "C7_SEAMS_NOT_FROM_START", "45 mm 牆階:板端縫 3659 的承接帶落在牆階面沒料的 18 mm 裡,沒有往內退到 3614", "左上起鋪,板長沿Y"),
    ("no_resettle", DSTEP, "C7_SEAMS_NOT_FROM_START", "雙牆階:退縫到 3614 後沒有再跑 G7,x>3300 那段只剩 13 mm 的收邊板條(應挪到 3587)", "左上起鋪,板長沿Y"),
    ("no_main_band_depth", STEP45, "C7_P182_TRACE_MISSING", "拿掉 P-182:y=3655 那面牆落在最後一支主支 [3646,3673] 的寬度裡,建構端卻沒有候選 trace", "左上起鋪,板長沿X"),
    ("p182_always", PIL2745, "C7_P182_FALSE_FAIL", "P-182 跳過第一段(主支寬度一跨牆就退):左牆壁柱 y 2745–2900,舊規則推開 8 mm、補併料就排得出,卻退縫到 2704", "左上起鋪,板長沿X"),
    ("p182_always", MIR54, "C7_P182_FALSE_FAIL", "同上,上下鏡像的 54 mm 牆階:R-butt 平移 1 mm 就排得出,卻退縫到 95;"
     "退縫後副支 [27,81] 的中線剛好在 y=54 牆線上,檢查也不能當掉", "左下起鋪,板長沿X"),
    ("p182_no_backface", DISTR, "C7_P182_TRACE_MISSING", "建構端不認背向起鋪側的牆:分辨房 x 0–300 的 y=3655 那面牆沒當成擋料,沒有候選", "左上起鋪,板長沿X"),
    ("p182_far_first", TRIPLE, "C7_P182_TRACE_INCOMPLETE", "候選由遠到近試:三段牆階先試 3609 就成功,比它優先的 3614 沒試", "左上起鋪,板長沿X"),
    ("p182_conflicts_only", PILCOL(1000), "C8_I19_PRIORITY", "候選只看衝突碼、不跑 check():壁柱加柱那間原縫位沒有衝突碼卻檢查紅,沒有退縫", "左上起鋪,板長沿X"),
]
for mut, room, want, why, *lay in MUTANTS:
    lt = next(l for l in fo.LAYOUTS if fo.layout_name(l) == lay[0]) if lay else LT_Y
    pp = dict(p, **room.get("params", {}))
    res = fo.build(room, lt, pp, frozenset(set(mut.split("+")) | {"skip_conflict_scan"}))
    try:
        got = {f["check"] for f in fo.check(res, pp)}
    except AssertionError as e_:  # 檢查本身當掉(例:中線剛好在牆線上)要明確報出來,不能只靠 exit 碼
        got = {"CHECK_CRASHED: " + (str(e_) or "AssertionError")}
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
        (STEP3720, "外框 3720、牆階牆 3690", "左上起鋪,板長沿X", "G7 照縫線上的對牆 3690 挪縫", ("a", 3649)),
        (STEP30, "30 mm 牆階", "左上起鋪,板長沿Y", "板端縫 G7 照 y=3670 牆挪縫", ("b", 3629)),
        (DSTEP, "雙牆階", "左上起鋪,板長沿Y", "板端縫先退到 3614,縫線伸進 x>3300 那段(對牆 3628),G7 再挪", ("b", 3587)),
        # P-182(推論):主支縫的對牆看主支整條寬度。審查員舉的例子與一個先由縫線 G7 挪、再由主支寬度退的例子
        (STEP45, "45 mm 牆階", "左上起鋪,板長沿X", "P-182:y=3655 牆落在主支寬度裡,主支縫退到 ⌊3655 − 40.5⌋", ("a", 3614)),
        (LROOM(4100, 3700, 1500, 54), "54 mm 牆階", "左上起鋪,板長沿X", "y=3646 剛好貼著主支起鋪側側面 [3646,3673],不算擋到主支,不退", ("a", 3659)),
        (LROOM(4100, 3700, 1500, 53), "53 mm 牆階", "右上起鋪,板長沿X", "P-182:主支縫退到 ⌊3647 − 40.5⌋", ("a", 3606)),
        (DSROOM(3649, 3597), "雙牆階 3649/3597", "左上起鋪,板長沿X", "P-182:先退到 3608,主支 [3595,3622] 又跨過 y=3597,G7 再退到 3556", ("a", 3556)),
        (DSROOM(3658, 3570), "雙牆階 3658/3570", "右上起鋪,板長沿X", "P-182:退到 3617,主支 [3604,3631] 不碰 y=3570,停在離原位最近的位置", ("a", 3617)),
        (DSROOM(3667, 3615), "雙牆階 3667/3615", "左上起鋪,板長沿X", "縫線 G7 先照 y=3667 挪到 3626,主支 [3613,3640] 跨過 y=3615,P-182 再退到 3574", ("a", 3574)),
        # 鏡像(上下翻轉、反向起鋪):縫位要是原房間的鏡像(3700 − 原值)
        (MIR54, "54 mm 牆階(上下鏡像)", "左下起鋪,板長沿X", "置中主支跨過 y=54 一 mm,R-butt 平移 1 mm 就不跨,不退(原房間 3659 的鏡像)", ("a", 41)),
        (MIRROR(LROOM(4100, 3700, 1500, 53), 1), "53 mm 牆階(上下鏡像)", "左下起鋪,板長沿X", "P-182 退到原房間 3606 的鏡像", ("a", 94)),
        (MIRROR(DSROOM(3649, 3597), 1), "雙牆階 3649/3597(上下鏡像)", "左下起鋪,板長沿X", "P-182 退到原房間 3556 的鏡像", ("a", 144)),
        # P-182(#251 審查 1b6b34f9、718cc9a3):原縫位不可行才退縫
        (T9COL(344), "牆階 344 mm + 柱", "左上起鋪,板長沿X", "舊規則往上推 2 mm 會壓到柱面料 [3681,3708],排不出;第二段照 y=3656 退", ("a", 3615)),
        (T9COL(342), "牆階 342 mm + 柱", "左上起鋪,板長沿X", "同上,照 y=3658 退", ("a", 3617)),
        (PIL2745, "左牆壁柱 y 2745–2900", "左上起鋪,板長沿X", "舊規則排得出(推開 8 mm、補併料),不退", ("a", 2750)),
        (PILW(4100, 3200, 2750, 2900, 200), "左牆壁柱 y 2750–2900", "左上起鋪,板長沿X", "縫線本身碰到壁柱面,照縫線上的對牆(G7)退,這是既有的不連續", ("a", 2709)),
        # P-182 第三版(#251 審查 718cc9a3)
        (PILCOL(1000), "壁柱 y 2745 加柱 x 1000", "左上起鋪,板長沿X", "原縫位檢查紅(C8 I19),退到 ⌊2745 − 40.5⌋", ("a", 2704)),
        (PILCOL(265), "壁柱 y 2745 加柱 x 265", "左上起鋪,板長沿X", "原縫位檢查紅(C8 I19、C10),退到 2704", ("a", 2704)),
        (S45COL, "45 mm 牆階加柱", "左上起鋪,板長沿X", "原縫位報 MAIN_HITS_RC_TIMBER,退到 3614", ("a", 3614)),
        (DISTR, "分辨房", "左上起鋪,板長沿X", "背向起鋪側的 y=3655 給 3614,但 3614 離 y=3654 那面牆不到 1.5w(C7b),再試 3613", ("a", 3613)),
        (DISTR, "分辨房", "右上起鋪,板長沿X", "同上", ("a", 3613)),
        (MIRROR(DISTR, 1), "分辨房(上下鏡像)", "左下起鋪,板長沿X", "鏡像:3720 − 3613", ("a", 107)),
        (MIRROR(DISTR, 1), "分辨房(上下鏡像)", "右下起鋪,板長沿X", "鏡像:3720 − 3613", ("a", 107)),
        (TRIPLE, "三段牆階", "左上起鋪,板長沿X", "近的候選 3614 不可行(C7b),3609 可行", ("a", 3609)),
        # 縫線「往起鋪側偏半 mm」的獨立期望值(#251 審查 1b6b34f9 須改 4):左牆壁柱下緣 y=1831 剛好在板端縫 1831 上,
        #   牆算在縫前面,G7 照它挪到 ⌊1831 − 40.5⌋ = 1790;探測線改成往對牆偏(建構端或兩邊一起)就停在 1831
        (PILW(3600, 3000, 1831, 2000, 200), "左牆壁柱 y 1831–2000", "左上起鋪,板長沿Y", "壁柱下緣剛好在縫線上,算在縫前面,板端縫挪到 1790", ("b", 1790))):
    res = fo.build(room_, next(l for l in fo.LAYOUTS if fo.layout_name(l) == lay_), p)
    fails = fo.check(res, p)
    got_seam = None if want_seam is None else res["seams_" + want_seam[0]][-1]
    ok = not res["conflicts"] and not fails and (want_seam is None or got_seam == want_seam[1])
    failed |= not ok
    seam_txt = "" if want_seam is None else f",最後一條{'板端縫' if want_seam[0] == 'b' else '縫'}要在 {want_seam[1]}(實得 {got_seam})"
    print(f"[{'綠' if ok else '錯!'}] 對照 {tag_} {lay_}:可施工({why_}{seam_txt})"
          f"{sorted({c['code'] for c in res['conflicts']})}{sorted({f['check'] for f in fails})}")
# P-182 第一段的實際排法要釘住(#251 審查 1b6b34f9):左牆壁柱 y 2745–2900,最後一支主支推開 8 mm 到 [2745,2772]、
#   併料 [2718,2745] 長 3846 mm(x 227–4073),整板 915、收邊板 449(2751–3200)
res = fo.build(PIL2745, next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左上起鋪,板長沿X"), p)
_m = [t for t in res["timbers"] if t["kind"] == "main" and t.get("seam") == 2750]
_d = [t for t in res["timbers"] if t.get("doubling")]
_ma = sorted({fo.rng(t["rect"], res["a"]) for t in _m})
_dl = sum(fo.rng(t["rect"], res["b"])[1] - fo.rng(t["rect"], res["b"])[0] for t in _d)
ok = (_ma == [(2745, 2772)] and [fo.rng(t["rect"], res["a"]) for t in _d] == [(2718, 2745)] and _dl == 3846
      and res["seams_a"][-1] == 2750 and not res["conflicts"] and not fo.check(res, p))
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] P-182 第一段:左牆壁柱 y 2745–2900 左上 X,主支 {_ma}(要 [(2745, 2772)]),併料 {[fo.rng(t['rect'], res['a']) for t in _d]} 長 {_dl}(要 3846),"
      f"縫 {res['seams_a'][-1]}(要 2750,收邊 449)")
# P-182 第三版:都不可行時才報衝突,trace 的每個候選都要真的失敗(#251 審查 718cc9a3)。外框深 3720、x>2600 那段只到 3665,
#   柱 x 1000–1400、y 3200–3620:原縫位 3667、退到 3624(y=3665)、再退到 3579(柱上面那面)都撞料;要報 P182_NO_FEASIBLE_CANDIDATE,
#   C7 自己算的候選集合也要是這三個,trace 每一個 C7 重跑 check() 都要失敗
DBLCOL = {"outer": [[0, 0], [4100, 0], [4100, 3665], [2600, 3665], [2600, 3720], [0, 3720]],
          "holes": [[[1000, 3200], [1400, 3200], [1400, 3620], [1000, 3620]]]}
res = fo.build(DBLCOL, next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左上起鋪,板長沿X"), p)
_tr = [e["seam"] for e in (res.get("p182") or {}).get("cands", [])]
_cs = fo.expected_p182_candidates(res["region"], res["a"], "min", 0, 3720, 3667, 2750, p["w"])
_pb = fo.p182_trace_problems(res, p)
ok = ("P182_NO_FEASIBLE_CANDIDATE" in {c["code"] for c in res["conflicts"]} and _tr == [3667, 3624, 3579] and _cs == [3667, 3624, 3579] and not _pb)
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] P-182 都不可行:trace {_tr}、C7 候選 {_cs}(都要 [3667, 3624, 3579]),trace 重跑 check() 沒失敗的 {_pb}(要沒有)")
# 牆線上取區間(檢查端 section_both_sides,#251 審查 1b6b34f9 建議 6):剛好在牆線上時取兩側都在室內的部分,正反兩個方向都要對
for room_, m_, want_ in ((LROOM(4100, 3700, 1500, 54), 3646, [(0, 2600)]), (MIR54, 54, [(0, 2600)])):
    got_ = [tuple(iv) for iv in fo.section_both_sides(fo.Region(room_["outer"], []), 1, m_)]
    ok = got_ == want_
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] 牆線 y={m_} 上的室內區間取兩側交集:要 {want_},實得 {got_}")
# C7b 專屬:把雙牆階的最後一條板端縫改回 3614(x>3300 那段只剩 13 mm),C7_G7_TOO_CLOSE 要報。只拿掉 C7b 時這一行轉紅。
res = fo.build(DSTEP, next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左上起鋪,板長沿Y"), p)
res["seams_b"] = res["seams_b"][:-1] + [3614]
got_ = {f["check"] for f in fo.check(res, p)}
ok = "C7_G7_TOO_CLOSE" in got_
failed |= not ok
print(f"[{'紅' if ok else '沒抓到!'}] tamper_seam        預期 C7_G7_TOO_CLOSE          實得 {sorted(got_)}  雙牆階的板端縫改回 3614:離 x>3300 的對牆只剩 13 mm")
# P-182 第三版 C7 的裁決(#251 審查 718cc9a3):對建構端的 candidate trace 動手腳,C7 都要抓到
import copy as _copy  # noqa: E402

_lx = next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左上起鋪,板長沿X")
_base45 = fo.build(STEP45, _lx, p)
_baseds = fo.build(DSROOM(3649, 3597), _lx, p)


def _tamper(base_, how):
    r_ = _copy.deepcopy(base_)
    how(r_)
    return {f["check"] for f in fo.check(r_, p)}


def _t_seam(r_):  # 主支縫改回 trace 判為失敗的原縫位
    r_["seams_a"] = r_["seams_a"][:-1] + [3659]


def _t_falsefail(r_):  # 原縫位那一筆換成選中的(可行的)佈局,仍標失敗
    r_["p182"]["cands"][0]["res"] = r_["p182"]["cands"][-1]["res"]


def _t_drop(r_):  # 雙牆階:拿掉 3608 那一筆
    r_["p182"]["cands"] = [e for e in r_["p182"]["cands"] if e["d"] != 3608]


def _t_noncand(r_):  # 選中一個不在候選集合裡的位置
    r_["seams_a"] = r_["seams_a"][:-1] + [3600]
    r_["p182"]["cands"].append(dict(_copy.copy(r_["p182"]["cands"][-1]), d=3600, seam=3600, ok=True))


def _t_skip(r_):  # 雙牆階:3608 標成可行卻沒選
    for e in r_["p182"]["cands"]:
        if e["d"] == 3608:
            e["ok"] = True


for nm_, base_, how_, want_, why_ in (
        ("tamper_main_seam", _base45, _t_seam, "C7_P182_CHOSE_FAILED", "45 mm 牆階的主支縫改回 3659(trace 判它不可行)"),
        ("tamper_false_fail", _base45, _t_falsefail, "C7_P182_FALSE_FAIL", "trace 把可行的佈局標成失敗"),
        ("tamper_trace_drop", _baseds, _t_drop, "C7_P182_TRACE_INCOMPLETE", "雙牆階 3649/3597:比選中的 3556 優先的 3608 不在 trace"),
        ("tamper_noncandidate", _base45, _t_noncand, "C7_P182_NOT_CANDIDATE", "選中 3600:不在 C7 自己算的候選集合"),
        ("tamper_skip_feasible", _baseds, _t_skip, "C7_P182_SKIPPED_FEASIBLE", "trace 說 3608 可行,卻選了 3556")):
    got_ = _tamper(base_, how_)
    ok = want_ in got_
    failed |= not ok
    print(f"[{'紅' if ok else '沒抓到!'}] {nm_:18s} 預期 {want_:24s} 實得 {sorted(got_)}  {why_}")
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
#   原因要是核心限制(主支頂延伸段),不是碰撞。P-182 會把這種情形退縫解掉,所以這裡關掉 P-182(no_main_band_depth),只看原縫位。
res = fo.build(STEP40, next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左上起鋪,板長沿X"), p, frozenset({"bbox_ft02", "no_main_band_depth"}))
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


def sweep_family(rooms_, mirror=False):
    """牆階這類房間的掃描:回傳 (不可施工集合, 可施工數, 檢查失敗清單, 原因次數, 建構次數)。
    mirror=True 時每間房上下、左右各翻一次,id 加上 |上下、|左右。正式掃描與 --mutants-only 的小型掃描共用這一個函式。"""
    unb_, nb_, bad_, codes_, n_ = set(), 0, [], {}, 0
    for rid_, room_ in rooms_:
        variants = [(rid_, room_)] if not mirror else [(f"{rid_}|{t_}", MIRROR(room_, k_)) for k_, t_ in ((1, "上下"), (0, "左右"))]
        for vid_, vroom_ in variants:
            for l_ in fo.LAYOUTS:
                n_ += 1
                r_ = fo.build(vroom_, l_, p)
                if r_["conflicts"]:
                    cs_ = tuple(sorted({c["code"] for c in r_["conflicts"]}))
                    for c in cs_:
                        codes_[c] = codes_.get(c, 0) + 1
                    unb_.add((vid_, fo.layout_name(l_), cs_))
                    pb_ = fo.p182_trace_problems(r_, p)  # 不可施工時,trace 裡每個候選都要真的失敗
                    if pb_:
                        bad_.append((vroom_["outer"], fo.layout_name(l_), ["P182_TRACE"] + [x[0] for x in pb_]))
                    continue
                nb_ += 1
                f_ = fo.check(r_, p)
                if f_:
                    bad_.append((vroom_["outer"], fo.layout_name(l_), sorted({f["check"] for f in f_})))
    return unb_, nb_, bad_, codes_, n_


def mirror_map(unb_step):
    """原房間的不可施工清單照鏡像對應(上下翻轉 上↔下、左右翻轉 左↔右)。"""
    return {(f"{r_}|{t_}", MIR_LAYOUT(l_, k_), c_) for r_, l_, c_ in unb_step for k_, t_ in ((1, "上下"), (0, "左右"))}


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
# 小型牆階與鏡像掃描(#251 審查 1b6b34f9 建議 5):--mutants-only 也要打到掃描端的翻轉、對應與比對;結果要和預期清單的對應部分一致
_ministeps = [("L_ch:20", LROOM(4100, 3700, 1500, 20)), ("L_ch:45", LROOM(4100, 3700, 1500, 45)),
              ("L_cw:20", LROOM(4100, 3700, 20, 1200)), ("DS:3649,3597", DSROOM(3649, 3597))]
_ids = {r_ for r_, _ in _ministeps}
_u0, _n0, _b0, _, _ = sweep_family(_ministeps)
_u1, _n1, _b1, _, _ = sweep_family(_ministeps, mirror=True)
_e0 = {(r_, l_, tuple(c_)) for r_, l_, c_ in _exp_all.get("step", []) if r_ in _ids}
_e1 = {(r_, l_, tuple(c_)) for r_, l_, c_ in _exp_all.get("step_mirror", []) if r_.split("|")[0] in _ids}
_cmp = [compare_unbuildable(_u0, _e0), compare_unbuildable(_u1, _e1), compare_unbuildable(_u1, mirror_map(_u0))]
ok = all(not x_ and not m_ for x_, m_ in _cmp) and not _b0 and not _b1 and _u0 and _u1
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] 小型牆階/鏡像掃描 {len(_ministeps)} 間:原房 {_n0} 次、鏡像 {_n1} 次,檢查失敗 {len(_b0) + len(_b1)};"
      f"和預期清單、鏡像對應的差異 {[(len(x_), len(m_)) for x_, m_ in _cmp]}")
# 引文逐字(#251 審查 178ba084 第 2、3 項):標成使用者原話的引文都要逐字出現在受測這棵樹的 決策佇列.md;缺了某一節的佇列要紅,而且要指出缺了哪一節;反例要抓到、正例要過
sys.path.insert(0, str(HERE))
import quote_check  # noqa: E402

try:
    _queue = quote_check.queue_from_tree()
except Exception as e_:  # 這棵樹沒有 決策佇列.md 就算失敗,不默默略過
    _queue = None
    failed = True
    print(f"[錯!] 引文逐字:讀不到 {quote_check.queue_source()}({e_.__class__.__name__})")
if _queue is not None:
    _nq, _badq = quote_check.scan(_queue)
    _wrongq = quote_check.self_check(_queue) + quote_check.missing_section_check(_queue)
    ok = not _badq and not _wrongq
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] 引文逐字({quote_check.queue_source()}):標成原話的引文 {_nq} 段都逐字出現在 決策佇列.md(不一致 {len(_badq)});"
          f"反例 {sum(1 for x_ in quote_check.SAMPLES if x_[1])} 個都抓到、正例 {sum(1 for x_ in quote_check.SAMPLES if not x_[1])} 個都過,"
          f"拿掉「{quote_check.MISSING_SECTION}」那一節的佇列要指出缺了這一節(判錯 {len(_wrongq)})")
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
unb = {"reflex": set(), "step": set(), "step_mirror": set()}
for rid, room in reflex_rooms:
    for l in fo.LAYOUTS:
        runs += 1
        res = fo.build(room, l, p)
        if res["conflicts"]:
            for c in res["conflicts"]:
                codes[c["code"]] = codes.get(c["code"], 0) + 1
            unb["reflex"].add((rid, fo.layout_name(l), tuple(sorted({c["code"] for c in res["conflicts"]}))))
            if fo.p182_trace_problems(res, p):
                rb.append((room["outer"], fo.layout_name(l), ["P182_TRACE"]))
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
unb["step"], sbuild, _sb, scodes, _n = sweep_family(step_rooms)
runs += _n
sbad = len(_sb)
rb += _sb
print(f"牆階 1–100 mm 的 L 形、壁龕與雙牆階 {len(step_rooms)} 間 × 8 種排法:可施工 {sbuild} 個,其中檢查失敗 {sbad} 個;"
      f"不可施工的排法數(依原因){scodes}")
# 鏡像:同一批房間上下、左右各翻一次。⌊w/2⌋ 與 ⌈w/2⌉ 不對稱,反向起鋪那半邊(back = ⌈w/2⌉)原本只有鏡像房才測得到。
unb["step_mirror"], mbuild, _mb, mcodes, _n = sweep_family(step_rooms, mirror=True)
runs += _n
mbad = len(_mb)
rb += _mb
print(f"鏡像(上下、左右)的牆階與雙牆階 {2 * len(step_rooms)} 間 × 8 種排法:可施工 {mbuild} 個,其中檢查失敗 {mbad} 個;"
      f"不可施工的排法數(依原因){mcodes}")
_x2, _m2 = compare_unbuildable(unb["step_mirror"], mirror_map(unb["step"]))
ok = not _x2 and not _m2
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] 鏡像對稱:鏡像房的不可施工清單等於原房間清單照鏡像對應;多出 {len(_x2)}、少了 {len(_m2)}")
for x in _x2[:10]:
    print("     多出", x)
for x in _m2[:10]:
    print("     少了", x)
# P-182 第三版的候選掃描(#251 審查 718cc9a3 的四族;快速模式取樣,--full 全跑)。可施工的都要通過全部檢查(含 C7 裁決),
#   不可施工的 trace 每個候選都要真的失敗;分辨房那一族另外要上下鏡像互為鏡像。
def _p182_family(name_, rooms_, mirror_pairs=False):
    """回傳 (次數, 可施工, 不可施工, 問題清單, 已知缺陷 C11 次數)。只有 C11_MAIN_NOT_BUTTED 的檢查失敗算已知缺陷
    (牆階加主支下方的柱,主支該貼住卻沒貼住;另開工單,本版不修),另外計數,不算失敗。"""
    n_ = nb_ = nu_ = k11_ = 0
    bad_ = []
    for key_, room_, lays_ in rooms_:
        for ln_ in lays_:
            l_ = next(l for l in fo.LAYOUTS if fo.layout_name(l) == ln_)
            r_ = fo.build(room_, l_, p)
            n_ += 1
            if r_["conflicts"]:
                nu_ += 1
                if fo.p182_trace_problems(r_, p):
                    bad_.append((key_, ln_, "trace"))
            else:
                nb_ += 1
                f_ = sorted({f["check"] for f in fo.check(r_, p)})
                if f_ == ["C11_MAIN_NOT_BUTTED"]:
                    k11_ += 1
                elif f_:
                    bad_.append((key_, ln_, f_))
            if mirror_pairs:
                m_ = fo.build(MIRROR(room_, 1), next(l for l in fo.LAYOUTS if fo.layout_name(l) == MIR_LAYOUT(ln_, 1)), p)
                c0_, c1_ = sorted({c["code"] for c in r_["conflicts"]}), sorted({c["code"] for c in m_["conflicts"]})
                if c0_ != c1_ or (not c0_ and abs(r_["seams_a"][-1] + m_["seams_a"][-1] - 3720) > 1):
                    bad_.append((key_, ln_, "mirror", r_["seams_a"][-1], m_["seams_a"][-1], c0_, c1_))
                elif not c1_ and fo.check(m_, p):
                    bad_.append((key_, ln_, "mirror-check"))
    return n_, nb_, nu_, bad_, k11_


_stp = 1 if FULL else 3
_fam = {}
_fam["t16 牆階 338–346 加柱"] = [((ch, kd, yc), {"outer": [[0, 0], [4100, 0], [4100, 4000 - ch], [2600, 4000 - ch], [2600, 4000], [0, 4000]],
                                               "holes": [[[1000, y0], [1400, y0], [1400, y1], [1000, y1]]]}, ["左上起鋪,板長沿X"])
                              for ch in (338, 340, 341, 342, 343, 344, 345, 346) for kd in ("below", "above") for yc in range(3600, 3740, 2 * _stp)
                              for y0, y1 in [((yc - 200, yc) if kd == "below" else (yc, yc + 200))] if y1 <= 3970 and y0 >= 2800]
_fam["t14 壁柱加柱"] = [((y0, x0), dict(PILW(4100, 3200, y0, 2900, 200), holes=[[[x0, 2650], [x0 + 300, 2650], [x0 + 300, 2850], [x0, 2850]]]),
                         [fo.layout_name(l) for l in fo.LAYOUTS]) for y0 in range(2741, 2750) for x0 in (400, 1000, 2000, 3000)]
_fam["t10 分辨房族(含鏡像)"] = [((e, F), {"outer": [[300, 0], [4100, 0], [4100, 3720], [0, 3720], [0, e], [300, e]] if F is None else
                                       [[300, 0], [4100, 0], [4100, F], [3800, F], [3800, 3720], [0, 3720], [0, e], [300, e]]},
                              ["左上起鋪,板長沿X", "右上起鋪,板長沿X", "左下起鋪,板長沿X", "右下起鋪,板長沿X"])
                             for e in range(3650, 3692, _stp) for F in (None, 3652, 3653, 3654, 3655, 3656, 3660)]
_fam["t4 牆階加柱"] = [((top, ch, kd, yc, cx), {"outer": [[0, 0], [4100, 0], [4100, top - ch], [2600, top - ch], [2600, top], [0, top]],
                                               "holes": [[[cx[0], y0], [cx[1], y0], [cx[1], y1], [cx[0], y1]]]}, ["左上起鋪,板長沿X"])
                       for top in (3700, 3720, 3740) for ch in range(1, 70, 2 * _stp) for kd in ("below", "above") for yc in range(3590, 3740, 3 * _stp)
                       for cx in ((1000, 1400), (3000, 3400))
                       for y0, y1 in [((yc - 200, yc) if kd == "below" else (yc, yc + 200))]
                       if y1 <= ((top - ch) if cx[0] >= 2600 else top) - 30 and y0 >= 2800]
for _nm, _rooms in _fam.items():
    _n, _nb, _nu, _bad, _k11 = _p182_family(_nm, _rooms, mirror_pairs=_nm.startswith("t10"))
    runs += _n
    ok = not _bad
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] P-182 候選掃描 {_nm}:{_n} 次,可施工 {_nb}、不可施工 {_nu};檢查失敗、trace 沒真的失敗、鏡像不對稱 {len(_bad)}"
          f"(已知缺陷 C11_MAIN_NOT_BUTTED {_k11} 次,另開工單)")
    for x in _bad[:8]:
        print("    ", x)
# 不可施工的排法要和明列的預期清單(每筆附原因代碼)完全一樣;清單空的就要 0 個。--write-expected 只在人工覆核後重寫清單。
if "--write-expected" in sys.argv:
    json.dump({fam: sorted([list(x[:2]) + [list(x[2])] for x in v]) for fam, v in unb.items()}, open(EXP_PATH, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=0)
expected_unb = json.load(open(EXP_PATH, encoding="utf-8"))
for fam in ("reflex", "step", "step_mirror"):
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
