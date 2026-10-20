"""framing_oracle 的自我測試。
(1) 突變:拿掉或弄偏某條規則,對應的檢查必須轉紅;未突變的對照組必須全綠。
    另跑 no_custom4(不套副支 custom 4):F1、F2 那 14 種排法都要被 C8_I19_PRIORITY 抓到,不多不少。
    剛好 min_piece(27 mm)的副支與柱面料必須放(T27 房);custom 4 的柱面料分支與寬向條件用合成案例驗。
(3c) 牆階 1–100 mm 的 L 形與壁龕 300 間、雙牆階 110 間,各 8 種排法,可施工的排法都要通過全部檢查。
     同一批房間再上下、左右各翻一次(鏡像),8 種排法:可施工的都要通過全部檢查,不可施工的要等於原房間的清單照鏡像對應
     (左上 ↔ 左下、左上 ↔ 右上),也要等於預期清單的 step_mirror 部分(#251 審查 392d4aa7 阻擋 1)。
用法另有 --mutants-only:只跑 (1)(2),跳過掃描。(1) 也包括引文逐字檢查(quote_check.py,讀受測這棵樹自己的 決策佇列.md)
    與掃描斷言比對函式 compare_unbuildable 的直接測試。
    P-182(最後一條主支縫的候選):手算對照組 HAND182(座標由規則手算,不從程式讀回;建構端與 C7 若一起算錯候選集合只靠它們抓得到)、
    trace 造假與檢查端盲點的 tamper 測試(C7 自己重建每個候選,不信 trace;check() 與 p182_trace_problems 都要報)。
    第 21 輪(#251 審查 92e64028):H6(退縫後的候選要補併料)與 TR182(15 間 P-182 對照房加 H6 轉置成板長沿 Y,各 4 種排法,縫位、trace 候選、衝突碼寫成常數),
    抓 build_candidate 只在板長沿 Y 出錯(BC_ax0)、候選不放併料(BC_no_doubling_cand);expected_for_scan 的過濾(只有 CI 取掃到的房間)直接測。
    第 22 輪(#318、#319):Region.inside 牆線上的探測點、三間缺角寬 = 房寬一半的 L 形房 × 8 種排法(縫位手算常數)、
    柱右面與牆階垂直牆同一條牆線(建構端報 CORE_LIMIT_BOUNDARY_END_FREE,突變 no_boundary_end_scan 釘著舊行為)、
    C3 承接帶跨房間分塊(H6 候選不放併料:板長沿 X 與轉置版都要被 C3 抓到)。
(2) 標準答案:F1–F5 與三個額外例子、8 種排法的輸出,必須與 oracle-golden.json 逐支相同。
(3b) 凹角、壁龕、獨立柱房 579 間與奇數縫寬矩形房,可施工的排法都要通過全部檢查。
(3) 掃描:矩形房。
    快速(--quick):實測時間見 README(和其他程序並行時明顯變慢)。
      - 一維逐 mm:寬 300–4000 × 深 2500,以及寬 2000 × 深 300–6000,只跑左上起鋪、板長沿 Y。
      - 二維 × 8 種排法:寬取 917k+{-43…-39,-1…2}(k=1–4,挪縫臨界帶)與每 331 mm;
        深取 1832k+{-43…-39,-1…2}(k=1–3)與每 617 mm。
    完整(--full):2026-10-19 在 b6856356 實跑 11684 秒(約 3 小時 15 分,nice 10)。
      - 一維逐 mm 掃描改跑全部 8 種排法。
      - 二維改為寬 917k±45、深 1832k±45 的整段邊界帶,加上每 97/211 mm 的網格。
用法: python selftest.py [--ci | --quick | --full | --mutants-only]
    不帶參數 = --ci:CI 模式(下角材列車的 run_all 用這個)。全部突變、標準答案逐支比對、全部手寫期望值的對照組、
        各類掃描的抽樣版本(固定步距或固定子集,決定性;鏡像也抽樣)。Windows 單獨跑目標 <= 300 s,實測秒數見 README。
    --quick:原本的快速全掃描(每次改動 oracle 程式的 PR 要附這個的收據,連同原始碼突變的收據)。
    --full:完整(一維也跑 8 種排法,二維取整段邊界帶);--mutants-only:只跑突變、對照組與標準答案(約 15 秒)。
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
MUTANTS_ONLY = "--mutants-only" in sys.argv  # 只跑 (1) 突變與 (2) 標準答案,跳過掃描(檢查紅燈用)
FULL = "--full" in sys.argv and not MUTANTS_ONLY
QUICK = "--quick" in sys.argv and not (FULL or MUTANTS_ONLY)  # 原本的快速全掃描(收據用)
CI = not (FULL or QUICK or MUTANTS_ONLY)  # 預設(不帶參數,或明寫 --ci)= CI 模式:給下角材列車的 run_all 用,Windows 單獨跑目標 <= 300 s
MODE = "mutants-only" if MUTANTS_ONLY else "full" if FULL else "quick" if QUICK else "ci"
# CI 模式的掃描取樣:全部是固定步距或固定子集(取每第 k 個),不用亂數,同一份程式每次結果相同。
#   rect1d:矩形房一維逐 mm 掃描取每第 k 個尺寸;band:二維挪縫臨界帶只取這幾個偏移(原本 9 個);grid_w、grid_h:二維網格的步距(原 331、617);
#   reflex:凹角、壁龕、獨立柱房取每第 k 間;step:牆階與雙牆階取每第 k 間(鏡像用同一批,所以鏡像也是抽樣);
#   p182:P-182 候選四族的取樣步距(quick 是 3,full 是 1);t14:壁柱加柱那族是固定清單,取每第 k 間;odd:奇數縫寬矩形房的尺寸步距放大幾倍
CI_SAMPLE = dict(rect1d=6, band=(-41, -1, 0, 1), grid_w=997, grid_h=1231, reflex=5, step=4, p182=9, t14=3, odd=2)
if "--write-expected" in sys.argv and CI:
    sys.exit("--write-expected 只能搭 --quick 或 --full(CI 模式只掃抽樣,寫出來的預期清單會缺)")
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


def TRANSPOSE(room):
    """x、y 對調(沿對角線翻轉),頂點順序反過來(對調是鏡射,不反過來頂點方向會變),孔一起轉。
    原本板長沿 X(主支縫沿 y,A 軸 = y)的房間變成板長沿 Y(主支縫沿 x,A 軸 = x)的房間;原房間的 y 就是新房間的 x。"""
    sw = lambda q: [q[1], q[0]]
    out = dict(room, outer=[sw(q) for q in reversed(room["outer"])])
    if room.get("holes"):
        out["holes"] = [[sw(q) for q in reversed(h)] for h in room["holes"]]
    return out


LAY = {fo.layout_name(l): l for l in fo.LAYOUTS}  # 排法名稱 → 排法


# 鏡像的 54 mm 牆階(審查員的反例):置中主支 [28,55] 只跨過 y=54 一 mm(⌊w/2⌋ 與 ⌈w/2⌉ 不對稱),R-butt 平移 1 mm 就不跨,不該退縫
MIR54 = MIRROR(LROOM(4100, 3700, 1500, 54), 1)
# 牆中段的壁柱(左牆 x 0–dx、y y0–y1),和審查員 r15 的 PIL 同一族
PILW = lambda W, H, y0, y1, dx: {"outer": [[0, 0], [W, 0], [W, H], [0, H], [0, y1], [dx, y1], [dx, y0], [0, y0]]}
# 1b6b34f9 審查的兩個退步(P-182 之後要恢復,第三版照樣要對):
#   (1) 牆階 + 柱:主支要讓開 y=3656 那面牆得往上推 2 mm,但會壓到柱下面的柱面料 [3681,3708];原縫位排不出,P-182 退到 3615(候選 ⌊3656 − 40.5⌋)
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
# #318 缺陷 1:柱 x 2600–3000、y 3444–3644 的右面(x=3000)剛好和牆階的垂直牆在同一條牆線上(sx=3000);sx=2900 是柱跨過它,sx=3100 是柱完全在它左邊
#   牆階 39 mm:x>sx 的牆在 y=3661,x<sx 的牆在 y=3700。柱下緣離 y=3661 的牆只有 17 mm,放不下 27 mm 的料
COLSTEP = lambda sx: {"outer": [[0, 0], [4100, 0], [4100, 3661], [sx, 3661], [sx, 3700], [0, 3700]],
                      "holes": [[[2600, 3444], [3000, 3444], [3000, 3644], [2600, 3644]]]}

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
     "(這間的主支推開 18 mm、補併料就排得出,原縫位可行,P-182 不會退縫補救;牆階 20–40 mm 那幾間原縫位排不出,P-182 照主支寬度裡的擋料退到同一處,照外框挪縫的錯在那裡看不出來)", "左上起鋪,板長沿X"),
    ("bbox_ft02", STEP30, "C7_SEAMS_NOT_FROM_START", "同上,板端縫(B 軸):30 mm 牆階應挪到 3629(40 mm 牆階時退縫規則也會退到同一處,抓不出差別,所以換這間)", "左上起鋪,板長沿Y"),
    ("bbox_ft02+no_push_fallback+no_main_band_depth", STEP40, "C1_OVERLAP", "照外框挪縫時,讓開牆料的平移撞到 y=3700 的牆料,沒有退回置中", "左上起鋪,板長沿X"),
    ("no_seam_retreat", STEP45, "C7_SEAMS_NOT_FROM_START", "45 mm 牆階:板端縫 3659 的承接帶落在牆階面沒料的 18 mm 裡,沒有往內退到 3614", "左上起鋪,板長沿Y"),
    ("no_resettle", DSTEP, "C7_SEAMS_NOT_FROM_START", "雙牆階:退縫到 3614 後沒有再跑 G7,x>3300 那段只剩 13 mm 的收邊板條(應挪到 3587)", "左上起鋪,板長沿Y"),
    ("no_main_band_depth", STEP45, "C7_P182_TRACE_MISSING", "拿掉 P-182:y=3655 那面牆落在最後一支主支 [3646,3673] 的寬度裡,建構端卻沒有候選 trace", "左上起鋪,板長沿X"),
    ("p182_always", PIL2745, "C7_P182_FALSE_FAIL", "P-182 跳過原縫位(主支寬度裡一有擋料就退):左牆壁柱 y 2745–2900,舊規則推開 8 mm、補併料就排得出,卻退縫到 2704", "左上起鋪,板長沿X"),
    ("p182_always", MIR54, "C7_P182_FALSE_FAIL", "同上,上下鏡像的 54 mm 牆階:R-butt 平移 1 mm 就排得出,卻退縫到 95;"
     "退縫後副支 [27,81] 的中線剛好在 y=54 牆線上,檢查也不能當掉", "左下起鋪,板長沿X"),
    ("p182_no_backface", DISTR, "C7_P182_TRACE_MISSING", "建構端不認背向起鋪側的牆:分辨房 x 0–300 的 y=3655 那面牆沒當成擋料,沒有候選", "左上起鋪,板長沿X"),
    ("p182_far_first", TRIPLE, "C7_P182_TRACE_INCOMPLETE", "候選由遠到近試:三段牆階先試 3609 就成功,比它優先的 3614 沒試", "左上起鋪,板長沿X"),
    ("p182_conflicts_only", PILCOL(1000), "C8_I19_PRIORITY", "候選只看衝突碼、不跑 check():壁柱加柱那間原縫位沒有衝突碼卻檢查紅,沒有退縫", "左上起鋪,板長沿X"),
    # #318 缺陷 1:拿掉建構端的邊界材端面判定(boundary_end_conflicts)就回到舊行為,建構端說可施工,完整 check() 卻紅(下面的對照組斷言有它時要報衝突)
    ("no_boundary_end_scan", COLSTEP(3000), "C8_I19_BOUNDARY_END", "柱右面 x=3000 與牆階垂直牆同一條牆線:牆階邊界材的端面落在沿柱料與沿牆料之間的缺口,沒有 boundary 可頂", "左上起鋪,板長沿X"),
    ("no_boundary_end_scan", COLSTEP(3000), "C3_EDGE_UNSUPPORTED", "同上:缺口裡的板邊沒有料承接", "左上起鋪,板長沿X"),
    ("no_boundary_end_scan", COLSTEP(3000), "C6_END_NOT_ON_TIMBER", "同上:沿柱料、沿牆料的端面一部分懸空", "左上起鋪,板長沿X"),
    ("no_boundary_end_scan", COLSTEP(2900), "C8_I19_BOUNDARY_END", "同上,牆階垂直牆改在 x=2900(柱跨過它)", "左上起鋪,板長沿X"),
]
for mut, room, want, why, *lay in MUTANTS:
    lt = next(l for l in fo.LAYOUTS if fo.layout_name(l) == lay[0]) if lay else LT_Y
    pp = dict(p, **room.get("params", {}))
    try:
        res = fo.build(room, lt, pp, frozenset(set(mut.split("+")) | {"skip_conflict_scan"}))
        got = {f["check"] for f in fo.check(res, pp)}
    except AssertionError as e_:  # 建構或檢查本身當掉(例:中線剛好在牆線上;P-182 評估候選時也會跑檢查)要明確報出來,不能只靠 exit 碼
        got = {"CRASHED: " + (str(e_) or "AssertionError")}
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
        (T9COL(344), "牆階 344 mm + 柱", "左上起鋪,板長沿X", "原縫位往上推 2 mm 會壓到柱面料 [3681,3708],排不出;P-182 照 y=3656 退", ("a", 3615)),
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
# P-182 原縫位候選的實際排法要釘住(#251 審查 1b6b34f9):左牆壁柱 y 2745–2900,最後一支主支推開 8 mm 到 [2745,2772]、
#   併料 [2718,2745] 長 3846 mm(x 227–4073),整板 915、收邊板 449(2751–3200)
res = fo.build(PIL2745, next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左上起鋪,板長沿X"), p)
_m = [t for t in res["timbers"] if t["kind"] == "main" and t.get("seam") == 2750]
_d = [t for t in res["timbers"] if t.get("doubling")]
_ma = sorted({fo.rng(t["rect"], res["a"]) for t in _m})
_dl = sum(fo.rng(t["rect"], res["b"])[1] - fo.rng(t["rect"], res["b"])[0] for t in _d)
ok = (_ma == [(2745, 2772)] and [fo.rng(t["rect"], res["a"]) for t in _d] == [(2718, 2745)] and _dl == 3846
      and res["seams_a"][-1] == 2750 and not res["conflicts"] and not fo.check(res, p))
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] P-182 原縫位:左牆壁柱 y 2745–2900 左上 X,主支 {_ma}(要 [(2745, 2772)]),併料 {[fo.rng(t['rect'], res['a']) for t in _d]} 長 {_dl}(要 3846),"
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
# P-182 手算對照組(#251 審查 4e1f1161,samewrong):建構端 p182_blockers 與 C7 expected_p182_candidates 若〈兩邊一起錯〉
#   (重疊判定都用 <= 、主支寬度都用 w 而不是 ⌈w/2⌉),所有〈兩邊是否一致〉的檢查都抓不到。這一組期望值由規則手算,座標不從程式讀回。
#   規則(README 推論表 P-182):候選 = 原縫位 d0,加上主支寬度內每一面擋料的 ⌊q − 1.5w⌋(q = 那面牆離起鋪牆的距離,w = 27);
#   擋料 = 與主支平行的牆,連同它室內那側 w 寬的料:室內在牆上方(+y)是 [q, q+27],在牆下方是 [q−27, q];
#   主支寬度 = [c − ⌈w/2⌉, c + ⌈w/2⌉] = [c − 14, c + 14];〈在寬度內〉= 與主支寬度有正寬度重疊(貼著邊、重疊 0 mm 不算)。
#   左上起鋪板長沿 X:縫沿 y,縫距 P + gap = 917,縫在 916、1833、2750、3667(房深 3720 或 4000,3667 ≤ 房深 − 40.5,G7 不挪),
#   d0 = 3667,主支寬度 [3653, 3681]。每間的推導寫在 HAND182 的說明欄。
HAND_LNOTCH = lambda F: {"outer": [[0, 0], [4100, 0], [4100, F], [3800, F], [3800, 3720], [0, 3720]]}  # x 3800–4100 的天花只到 y = F
HAND_POCKET = lambda e, F, H=3720: {"outer": [[300, 0], [4100, 0], [4100, F], [3800, F], [3800, H], [0, H], [0, e], [300, e]]}  # 左端 x 0–300 的室內從 y = e 起
HAND_POCKET_ONLY = lambda e, H: {"outer": [[300, 0], [4100, 0], [4100, H], [0, H], [0, e], [300, e]]}
HAND182 = [
    # (名稱, 房間, 排法, 期望的 trace 縫位(None = 沒有 trace), 期望的最後一條主支縫, 推導)
    ("H1 貼著寬度下緣", HAND_LNOTCH(3653), "左上起鋪,板長沿X", None, 3667,
     "x 3800–4100 的牆 y=3653,室內在牆下方,擋料 [3626,3653];主支寬度 [3653,3681],重疊 0 mm(貼著邊),不算擋料。其他牆的擋料 [0,27]、[3693,3720] 都離得遠。"
     "候選集合只有 d0 = 3667,沒有 trace;沿用原縫位 3667(主支 [3654,3681] 只存在於 x < 3800,碰不到 x ≥ 3800 的牆料)"),
    ("H1' 重疊 1 mm", HAND_LNOTCH(3654), "左上起鋪,板長沿X", [3667], 3667,
     "同上但牆 y=3654,擋料 [3627,3654] 與 [3653,3681] 重疊 1 mm,算擋料:候選多一個 ⌊3654 − 40.5⌋ = 3613;"
     "原縫位 3667 可行(主支只存在於 x < 3800),選原縫位,trace 只有原縫位一筆"),
    ("H2 貼著寬度上緣", HAND_POCKET_ONLY(3681, 4000), "左上起鋪,板長沿X", None, 3667,
     "房深 4000,x 0–300 的室內從 y=3681 起,牆 y=3681 的擋料 [3681,3708];主支寬度 [3653,3681],重疊 0 mm(貼著邊),不算。沒有 trace,3667"),
    ("H2' 重疊 1 mm", HAND_POCKET_ONLY(3680, 4000), "左上起鋪,板長沿X", [3667], 3667,
     "牆 y=3680,擋料 [3680,3707] 與 [3653,3681] 重疊 1 mm,算擋料:候選多一個 ⌊3680 − 40.5⌋ = 3639;原縫位可行(主支從 x=327 起,碰不到 x < 300 的牆料),選原縫位"),
    ("H3 寬度 w 對 ⌈w/2⌉", HAND_POCKET(3650, 3652), "左上起鋪,板長沿X", [3667, 3609], 3609,
     "牆 y=3652(x 3800–4100,室內在下方)擋料 [3625,3652],離主支寬度 [3653,3681] 差 1 mm,不是擋料(若主支寬度誤算成 [c − 27, c + 27] = [3640,3694] 就會是,多出候選 ⌊3652 − 40.5⌋ = 3611,"
     "排在 3609 前面而被選中)。牆 y=3650(x 0–300,室內在上方)擋料 [3650,3677] 與 [3653,3681] 重疊 24 mm,是擋料:候選 ⌊3650 − 40.5⌋ = 3609。"
     "原縫位 3667 的主支 [3654,3681] 在 x 27–300 撞到牆 y=3650 的擋料 [3650,3677],不可行;退到 3609:寬度 [3595,3623] 裡沒有擋料,可行"),
    ("H4 外框 3653/3650(審查員 samewrong)", HAND_POCKET(3650, 3653), "左上起鋪,板長沿X", [3667, 3609], 3609,
     "外框 [[300,0],[4100,0],[4100,3653],[3800,3653],[3800,3720],[0,3720],[0,3650],[300,3650]]。牆 y=3653(x 3800–4100)擋料 [3626,3653] 貼著 [3653,3681] 的下緣,重疊 0 mm,不是擋料"
     "(若重疊判定誤用 <= 或主支寬度誤用 w,多出候選 ⌊3653 − 40.5⌋ = 3612,排在 3609 前面而被選中)。牆 y=3650 的擋料 [3650,3677] 是擋料:候選 3609。"
     "原縫位 3667 不可行(主支撞到 [3650,3677]),3609 可行(寬度 [3595,3623] 裡沒有擋料)。選 3609"),
    ("H5 寬度 w 對 ⌈w/2⌉(可行時)", HAND_LNOTCH(3645), "左上起鋪,板長沿X", None, 3667,
     "牆 y=3645,擋料 [3618,3645];離主支寬度 [3653,3681] 差 8 mm,不是擋料(若主支寬度誤算成 [3640,3694] 就會是,於是多出 trace)。沒有 trace,3667"),
    # 第 21 輪(#251 審查 92e64028):退縫後的候選自己也要補併料(審查員的 BC_no_doubling_cand:候選不放併料),以前沒有任何對照房抓得到
    ("H6 退縫後的候選要補併料", HAND_POCKET(3646, 3600), "左上起鋪,板長沿X", [3667, 3605], 3605,
     "x 0–300 的室內從 y=3646 起(牆 y=3646,室內在上方),擋料 [3646,3673] 與原縫位 3667 的主支寬度 [3653,3681] 重疊 20 mm,是擋料:候選多一個 ⌊3646 − 40.5⌋ = 3605。"
     "x 3800–4100 的天花只到 y=3600(室內在下方),擋料 [3573,3600] 離 [3653,3681] 很遠,不是原縫位的擋料。原縫位 3667 不可行(主支撞到 [3646,3673])。"
     "候選 3605 的主支置中 [3592,3619],與 y=3600 的擋料 [3573,3600] 重疊 8 mm,超過承接容許量(往上平移上限 ⌊27/2⌋ − 1 − 8 = 4 mm),"
     "主支往上貼到 [3600,3627],下面那一側的板邊承接要補併料 [3573,3600](下面的 H6 實際排法斷言)。選 3605"),
]
for nm_, room_, lay_, want_trace_, want_seam_, why_ in HAND182:
    res = fo.build(room_, next(l for l in fo.LAYOUTS if fo.layout_name(l) == lay_), p)
    got_trace_ = None if not res.get("p182") else [e["seam"] for e in res["p182"]["cands"]]
    ok = (got_trace_ == want_trace_ and res["seams_a"][-1] == want_seam_ and not res["conflicts"] and not fo.check(res, p))
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] P-182 手算 {nm_}:trace 縫位 {got_trace_}(要 {want_trace_}),最後一條主支縫 {res['seams_a'][-1]}(要 {want_seam_}),"
          f"衝突 {sorted({c['code'] for c in res['conflicts']})},檢查失敗 {sorted({f['check'] for f in fo.check(res, p)}) if not res['conflicts'] else '略'}")
# 上下鏡像:左下起鋪,縫位是 3720 − 原值(H4:3720 − 3609 = 111;H1':房深 3720,縫 53)。擋料上下對調,結果要是原房間的鏡像
for nm_, room_, lay_, want_trace_, want_seam_ in (
        ("H4 鏡像", MIRROR(HAND_POCKET(3650, 3653), 1), "左下起鋪,板長沿X", [53, 111], 111),
        ("H1' 鏡像", MIRROR(HAND_LNOTCH(3654), 1), "左下起鋪,板長沿X", [53], 53),
        ("H1 鏡像", MIRROR(HAND_LNOTCH(3653), 1), "左下起鋪,板長沿X", None, 53)):
    res = fo.build(room_, next(l for l in fo.LAYOUTS if fo.layout_name(l) == lay_), p)
    got_trace_ = None if not res.get("p182") else [e["seam"] for e in res["p182"]["cands"]]
    ok = (got_trace_ == want_trace_ and res["seams_a"][-1] == want_seam_ and not res["conflicts"] and not fo.check(res, p))
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] P-182 手算 {nm_}:trace 縫位 {got_trace_}(要 {want_trace_}),最後一條主支縫 {res['seams_a'][-1]}(要 {want_seam_})")
# H6 的實際排法要釘住(退縫後的候選自己要補併料):選中的 3605 的最後一支主支 [3600,3627](置中 [3592,3619] 往上貼到 y=3600 的擋料 [3573,3600]),
#   併料恰一支、貼在主支下面 y 3573–3600。候選建構若不放併料(審查員的 BC_no_doubling_cand),下面那一側板邊承接不足(C3),候選變成不可行,選到別處
_h6 = HAND_POCKET(3646, 3600)
res = fo.build(_h6, LAY["左上起鋪,板長沿X"], p)
_m = sorted({fo.rng(t["rect"], res["a"]) for t in res["timbers"] if t["kind"] == "main" and t.get("seam") == 3605})
_d = sorted(fo.rng(t["rect"], res["a"]) for t in res["timbers"] if t.get("doubling"))
ok = _m == [(3600, 3627)] and _d == [(3573, 3600)] and res["seams_a"][-1] == 3605 and not res["conflicts"] and not fo.check(res, p)
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] P-182 H6:選中的 3605 的主支 {_m}(要 [(3600, 3627)]),併料 {_d}(要 [(3573, 3600)],恰一支),縫 {res['seams_a'][-1]}(要 3605)")
# P-182 板長沿 Y(#251 審查 92e64028 須改 1):上面的 P-182 對照房全是板長沿 X(主支縫沿 y,A 軸 = y)。板長沿 Y 時主支縫沿 x(A 軸 = x),
#   建構端的 build_candidate 若只在 A 軸 = x 才出錯(審查員的 BC_ax0:非原縫位候選的最後一支主支移 15 mm),上面全綠。
#   這一組把 15 間 P-182 對照房加上 H6 轉置(x、y 對調,頂點反序,孔一起轉)後各跑 4 種排法,用手寫的常數釘住:最後一條主支縫、
#   trace 的候選縫位、衝突碼。期望值是常數,不從程式讀回,也不在這裡從原房間現算。來源:
#   - 左上、左下起鋪(從 x 小的那一側起鋪)對應原房間從 y 小的那一側起鋪:縫位與候選就是上面各房釘過的值(HAND182 與 want_seam 那一串),轉置只換座標軸;
#   - 右上、右下起鋪(從 x 大的那一側起鋪)的對牆是 x = 0 那面平的牆(轉置前的 y = 0),沒有 P-182、沒有 trace。縫距 917,縫在離起鋪牆 916、1833、2750、3667:
#     房深 ≥ 3720 時最後一條縫離起鋪牆 3667(深 3720 → 縫在 3720 − 3667 = 53,深 4000 → 333);深 3700 時 3667 > ⌊3700 − 40.5⌋ = 3659,G7 挪到 3659(縫在 3700 − 3659 = 41);
#     深 3200 的壁柱房只有 916、1833、2750 三條(下一條 3667 > 3200),縫在 3200 − 2750 = 450;
#   - DBLCOL 從 x 大的那一側起鋪:牆 y=3665 的擋料 [3638,3665] 與柱上緣的柱面料 [3620,3647] 重疊 9 mm(兩支沿牆料互撞),報 TIMBERS_COLLIDE。
#   (房間, 左上/左下 Y 的 trace 縫位, 左上/左下 Y 的最後一條主支縫, 左上/左下 Y 的衝突碼, 右上/右下 Y 的最後一條主支縫, 右上/右下 Y 的衝突碼)
TR182 = [
    ("STEP45", STEP45, [3659, 3614], 3614, [], 41, []),
    ("L53", LROOM(4100, 3700, 1500, 53), [3659, 3606], 3606, [], 41, []),
    ("DS3649,3597", DSROOM(3649, 3597), [3659, 3608, 3556], 3556, [], 41, []),
    ("DS3658,3570", DSROOM(3658, 3570), [3659, 3617], 3617, [], 41, []),
    ("DS3667,3615", DSROOM(3667, 3615), [3626, 3574], 3574, [], 41, []),
    ("T9COL344", T9COL(344), [3667, 3615], 3615, [], 333, []),
    ("PILCOL1000", PILCOL(1000), [2750, 2704], 2704, [], 450, []),
    ("PILCOL265", PILCOL(265), [2750, 2704], 2704, [], 450, []),
    ("S45COL", S45COL, [3659, 3614], 3614, [], 41, []),
    ("DISTR", DISTR, [3667, 3614, 3613], 3613, [], 53, []),
    ("TRIPLE", TRIPLE, [3659, 3614, 3609], 3609, [], 41, []),
    ("DBLCOL", DBLCOL, [3667, 3624, 3579], 3667, ["P182_NO_FEASIBLE_CANDIDATE"], 53, ["TIMBERS_COLLIDE"]),
    ("H3", HAND_POCKET(3650, 3652), [3667, 3609], 3609, [], 53, []),
    ("H4", HAND_POCKET(3650, 3653), [3667, 3609], 3609, [], 53, []),
    ("PIL2745", PIL2745, [2750], 2750, [], 450, []),
    ("H6", HAND_POCKET(3646, 3600), [3667, 3605], 3605, [], 53, []),
]
#   併料(左上、左下起鋪,只列手算得出的兩間):H6 的併料 y 3573–3600 轉置後是 x 3573–3600(貼在主支 [3600,3627] 的低側);
#   PIL2745 原縫位 2750 的主支推開 8 mm 到 [2745,2772],併料 [2718,2745] 長 3846(上面 X 版已釘)。審查員的 BC_no_doubling_cand 在轉置版
#   會讓候選 3605 的 C3 照樣全過(第 21 輪發現:C3 的承接帶被房間分塊截斷,見 README 已知缺口),所以這裡要直接釘併料,不能只靠 check()
TR182_DBL = {"H6": [(3573, 3600)], "PIL2745": [(2718, 2745)]}
for nm_, room_, tr_min_, seam_min_, cs_min_, seam_max_, cs_max_ in TR182:
    troom_, bad_ = TRANSPOSE(room_), []
    for lay_, from_min_ in (("左上起鋪,板長沿Y", True), ("左下起鋪,板長沿Y", True), ("右上起鋪,板長沿Y", False), ("右下起鋪,板長沿Y", False)):
        want_ = (tr_min_, seam_min_, cs_min_) if from_min_ else (None, seam_max_, cs_max_)
        try:
            res = fo.build(troom_, LAY[lay_], p)
            got_ = (None if not res.get("p182") else [e["seam"] for e in res["p182"]["cands"]], res["seams_a"][-1],
                    sorted({c["code"] for c in res["conflicts"]}))
            if from_min_ and nm_ in TR182_DBL:  # 併料的 A 軸範圍(沿 x)與長度
                dbl_ = sorted(fo.rng(t["rect"], res["a"]) for t in res["timbers"] if t.get("doubling"))
                if dbl_ != TR182_DBL[nm_] or (nm_ == "PIL2745" and sum(fo.rng(t["rect"], res["b"])[1] - fo.rng(t["rect"], res["b"])[0]
                                                                  for t in res["timbers"] if t.get("doubling")) != 3846):
                    got_ = got_ + ("併料", dbl_)
            # 可施工的要通過全部檢查(C7 的 P-182 裁決在內);不可施工的,trace 的每個候選 C7 重建後都要真的失敗
            why_ = fo.p182_trace_problems(res, p) if res["conflicts"] else fo.check(res, p)
        except AssertionError as e_:  # 建構或檢查當掉也要明確報出來
            got_, why_ = None, [("CRASHED", str(e_) or "AssertionError")]
        if got_ != want_ or why_:
            bad_.append((lay_, got_, want_, [x if isinstance(x, tuple) else x["check"] for x in why_]))
    ok = not bad_
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] P-182 板長沿 Y(轉置){nm_:12s} 4 種排法:左上/左下 trace {tr_min_} 縫 {seam_min_}{cs_min_ or ''},右上/右下縫 {seam_max_}{cs_max_ or ''}")
    for x_ in bad_:
        print("     ", x_)
# ---------------------------------------------------------------- #318 缺陷 2、缺陷 1 與 #319 的對照組(期望值都是手寫常數,不從程式讀回)
# (a) 牆線上的探測點(#318 缺陷 2):建構端問〈這條牆邊的哪一側是室內〉,探測點是牆邊中點往室內側偏 0.5 mm。L 形缺角寬 = 房寬一半時,
#     下緣水平邊的中點 x 就是凹角的 x(牆線):垂直切線穿過牆端,_ring_section 只數嚴格跨過的邊,奇偶不保證是偶數,以前當掉(AssertionError)。
#     室內與否由圖形手寫:LROOM(3600,3000,1800,1000) = [[0,0],[3600,0],[3600,2000],[1800,2000],[1800,3000],[0,3000]],
#     室內 = x 0–3600 × y 0–2000 加 x 0–1800 × y 2000–3000;孔例 = STEP45 外框(牆階垂直牆 x=2600)加孔 x 2500–2700 × y 500–800(孔的水平邊中點 x 也是 2600)。
_inside_reg = {"L": fo.Region(LROOM(3600, 3000, 1800, 1000)["outer"], []),
               "H": fo.Region(STEP45["outer"], [[[2500, 500], [2700, 500], [2700, 800], [2500, 800]]])}
_inside_cases = (
    ("L", 1800, 0.5, True), ("L", 1800, -0.5, False),       # 下緣水平邊的中點(x = 1800 = 凹角的 x):往室內側、往室外側
    ("L", 1800, 1999.5, True), ("L", 1800, 3000.5, False),  # 凹角正下方在室內;上緣延長線的上方在室外
    ("L", 900, 2999.5, True), ("L", 900, 3000.5, False),    # 上緣水平邊的中點(x = 900 不在牆線上:維持舊路徑)
    ("L", 2700, 1999.5, True), ("L", 2700, 2000.5, False),  # 缺角下緣水平邊的中點(x = 2700,不在牆線上)
    ("H", 2600, 499.5, True), ("H", 2600, 500.5, False),    # 孔下緣水平邊的中點 x = 2600 = 牆階垂直牆的 x
    ("H", 2600, 799.5, False), ("H", 2600, 800.5, True))    # 孔上緣
_bad_in = []
for k_, x_, y_, want_ in _inside_cases:
    try:
        got_ = _inside_reg[k_].inside(x_, y_)
    except AssertionError as e_:
        got_ = "CRASHED: " + (str(e_) or "AssertionError")
    if got_ != want_:
        _bad_in.append((k_, x_, y_, want_, got_))
ok = not _bad_in
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] #318 缺陷 2 Region.inside 牆線上的探測點 {len(_inside_cases)} 個:不一致 {_bad_in}")
# (b) 三間 L 形房(缺角寬 = 房寬一半)× 8 種排法:縫位是手算的常數,全部要可施工、檢查全過(不當掉)。
#     縫距:主支縫(板寬 915、縫 2)首縫離起鋪牆 916,之後每 917;板端縫(板長 1830)首縫 1831,之後每 1832;
#     下一片板的起點仍在對牆之內(深度 > 縫距的 k+1 倍)才有第 k+1 條縫。G7:最後一條縫離縫線上最近的對牆不到 1.5w = 40.5 才挪;
#     這三間的最後一條縫離對牆都 ≥ 169 mm(最近的是缺角下緣 y=2000 與板端縫 1831 的 169),所以沒有挪動。
#     從座標大的那側起鋪(max)時縫位 = 房邊界 − 距離(缺角在 +x、+y 的角,x = 0、y = 0 的對牆是平的)。
#     yP = 主支縫沿 y(板長沿 X)、xL = 板端縫沿 x(板長沿 X)、xP = 主支縫沿 x(板長沿 Y)、yL = 板端縫沿 y(板長沿 Y);每個清單是 (min 側起鋪, max 側起鋪)。
#     P-182:最後一條主支縫離與它平行的牆都 ≥ 250 mm(主支寬度只有縫兩側各 14 mm),寬度裡沒有擋料,所以沒有候選、沒有 trace。
_L318 = (
    ("L 3600×3000 缺 1800×1000", LROOM(3600, 3000, 1800, 1000),
     dict(yP=([916, 1833, 2750], [250, 1167, 2084]), xL=([1831], [1769]),
          xP=([916, 1833, 2750], [850, 1767, 2684]), yL=([1831], [1169]))),
    ("L 4000×3000 缺 2000×1000", LROOM(4000, 3000, 2000, 1000),
     dict(yP=([916, 1833, 2750], [250, 1167, 2084]), xL=([1831, 3663], [337, 2169]),
          xP=([916, 1833, 2750, 3667], [333, 1250, 2167, 3084]), yL=([1831], [1169]))),
    ("L 5000×4000 缺 2500×1600", LROOM(5000, 4000, 2500, 1600),
     dict(yP=([916, 1833, 2750, 3667], [333, 1250, 2167, 3084]), xL=([1831, 3663], [1337, 3169]),
          xP=([916, 1833, 2750, 3667, 4584], [416, 1333, 2250, 3167, 4084]), yL=([1831, 3663], [337, 2169]))))
_L318_LAY = {"左上起鋪,板長沿X": (("yP", 0), ("xL", 0)), "右上起鋪,板長沿X": (("yP", 0), ("xL", 1)),
             "左下起鋪,板長沿X": (("yP", 1), ("xL", 0)), "右下起鋪,板長沿X": (("yP", 1), ("xL", 1)),
             "左上起鋪,板長沿Y": (("xP", 0), ("yL", 0)), "左下起鋪,板長沿Y": (("xP", 0), ("yL", 1)),
             "右上起鋪,板長沿Y": (("xP", 1), ("yL", 0)), "右下起鋪,板長沿Y": (("xP", 1), ("yL", 1))}
for nm_, room_, lists_ in _L318:
    bad_ = []
    for ln_, ((ka_, sa_), (kb_, sb_)) in _L318_LAY.items():
        want_ = (lists_[ka_][sa_], lists_[kb_][sb_], [], [])  # (主支縫, 板端縫, 衝突碼, 檢查失敗)
        try:
            res = fo.build(room_, LAY[ln_], p)
            fl_ = [] if res["conflicts"] else fo.check(res, p)
            got_ = (sorted(res["seams_a"]), sorted(res["seams_b"]), sorted({c["code"] for c in res["conflicts"]}), sorted({f["check"] for f in fl_}))
        except AssertionError as e_:
            got_ = ("CRASHED", str(e_) or "AssertionError")
        if got_ != want_:
            bad_.append((ln_, got_, want_))
    ok = not bad_
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] #318 缺陷 2 {nm_}:8 種排法的縫位(手算)、可施工、檢查全過;不一致 {len(bad_)}")
    for x_ in bad_:
        print("     ", x_)
    # 同一間的上下鏡像、左右鏡像、轉置(x、y 對調)也要全部可施工、檢查全過、不當掉(縫位不逐一釘,鏡像的縫位差 ⌊w/2⌋ 與 ⌈w/2⌉ 那 1 mm 的對稱性不在這裡驗)
    bad_ = []
    for vn_, vroom_ in (("上下鏡像", MIRROR(room_, 1)), ("左右鏡像", MIRROR(room_, 0)), ("轉置", TRANSPOSE(room_))):
        for l_ in fo.LAYOUTS:
            try:
                res = fo.build(vroom_, l_, p)
                fl_ = [] if res["conflicts"] else fo.check(res, p)
                got_ = (sorted({c["code"] for c in res["conflicts"]}), sorted({f["check"] for f in fl_}))
            except AssertionError as e_:
                got_ = ("CRASHED", str(e_) or "AssertionError")
            if got_ != ([], []):
                bad_.append((vn_, fo.layout_name(l_), got_))
    ok = not bad_
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] #318 缺陷 2 {nm_} 的上下/左右鏡像與轉置 24 種排法:全部可施工、檢查全過;不一致 {len(bad_)}")
    for x_ in bad_[:6]:
        print("     ", x_)
# (c) 缺陷 2 的第二個最小重現:孔的水平邊中點 x 對上外框別處頂點的 x(STEP45 的牆階垂直牆 x=2600)。8 種排法不當掉;
#     可施工的檢查全過;不可施工的 P-182 trace 每個候選都要真的失敗(和其他掃描同一條件)。沒有孔的 STEP45 左上 X 縫 3614、左上 Y 縫 3667(上面已釘),孔離牆階很遠。
for nm_, room_ in (("STEP45 加孔 x 2500–2700 y 500–800", dict(STEP45, holes=[[[2500, 500], [2700, 500], [2700, 800], [2500, 800]]])),
                   ("STEP45 加孔 x 2400–2800 y 1000–1300", dict(STEP45, holes=[[[2400, 1000], [2800, 1000], [2800, 1300], [2400, 1300]]]))):
    bad_, nbuild_ = [], 0
    for l_ in fo.LAYOUTS:
        try:
            res = fo.build(room_, l_, p)
            if res["conflicts"]:
                pb_ = fo.p182_trace_problems(res, p)
                got_ = ["P182_TRACE"] + [x[0] for x in pb_] if pb_ else []
            else:
                nbuild_ += 1
                got_ = sorted({f["check"] for f in fo.check(res, p)})
        except AssertionError as e_:
            got_ = ["CRASHED: " + (str(e_) or "AssertionError")]
        if got_:
            bad_.append((fo.layout_name(l_), got_))
    ok = not bad_
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] #318 缺陷 2 {nm_}:8 種排法不當掉,可施工 {nbuild_} 個的檢查全過、不可施工的 trace 沒問題;不一致 {len(bad_)}")
    for x_ in bad_:
        print("     ", x_)
# (d) 缺陷 2 的小型掃描:L 形缺角寬 = 房寬一半(原本的 L 形掃描每 457 mm 取一次缺角寬,永遠跳過 W/2),W、H 取原掃描的值、缺角高取 3 個,共 27 間 × 8 種排法。
#     性質檢查(不釘縫位):不當掉;可施工的檢查全過;不可施工的 trace 沒問題。不可施工的數量只印出來(原 L 形掃描是 0 個)。
_w2_bad, _w2_n, _w2_unb = [], 0, 0
for W_ in (3000, 4100, 5000):
    for H_ in (2600, 3700, 4800):
        for ch_ in (300, 913, 1526):
            room_ = LROOM(W_, H_, W_ // 2, ch_)
            for l_ in fo.LAYOUTS:
                _w2_n += 1
                try:
                    res = fo.build(room_, l_, p)
                    if res["conflicts"]:
                        _w2_unb += 1
                        got_ = ["P182_TRACE"] if fo.p182_trace_problems(res, p) else []
                    else:
                        got_ = sorted({f["check"] for f in fo.check(res, p)})
                except AssertionError as e_:
                    got_ = ["CRASHED: " + (str(e_) or "AssertionError")]
                if got_:
                    _w2_bad.append((W_, H_, ch_, fo.layout_name(l_), got_))
ok = not _w2_bad
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] #318 缺陷 2 缺角寬 = 房寬一半的 L 形 {_w2_n} 個排法:不當掉、可施工的檢查全過;不一致 {len(_w2_bad)}(不可施工 {_w2_unb} 個,預期 0)")
for x_ in _w2_bad[:6]:
    print("     ", x_)
# (e) 缺陷 1:柱右面(x=3000)與牆階垂直牆在同一條牆線上。以前建構端說可施工(沒有衝突碼),完整 check() 紅 C3、C6、C8(上面的突變 no_boundary_end_scan 釘著舊行為);
#     現在建構端直接報核心限制 CORE_LIMIT_BOUNDARY_END_FREE(牆階邊界材的端面落在沿柱料與沿牆料之間的缺口,核心 I19 不准它頂非 boundary 的料)。
#     物理上這種房間能不能施工沒有確認,這裡只釘〈建構端與檢查端一致〉:報衝突;柱完全在牆階左邊(x=3100)時照舊可施工、全過(#318 正文:全過)。
#     牆階 39 mm、柱下緣離 y=3661 的牆 17 mm(放不下 27 mm 的料),左右鏡像的房間也要同樣報。
for nm_, room_, lay_, want_codes_, want_fail_ in (
        ("柱右面 = 牆階垂直牆(x=3000)", COLSTEP(3000), "左上起鋪,板長沿X", ["CORE_LIMIT_BOUNDARY_END_FREE"], None),
        ("柱跨過牆階垂直牆(x=2900)", COLSTEP(2900), "左上起鋪,板長沿X", ["CORE_LIMIT_BOUNDARY_END_FREE"], None),
        ("牆階垂直牆在柱右邊(x=3100)", COLSTEP(3100), "左上起鋪,板長沿X", [], []),
        ("左右鏡像:柱左面 = 牆階垂直牆(x=1100)", MIRROR(COLSTEP(3000), 0), "右上起鋪,板長沿X", ["CORE_LIMIT_BOUNDARY_END_FREE"], None)):
    try:
        res = fo.build(room_, LAY[lay_], p)
        got_codes_ = sorted({c["code"] for c in res["conflicts"]})
        got_fail_ = None if res["conflicts"] else sorted({f["check"] for f in fo.check(res, p)})
    except AssertionError as e_:
        got_codes_, got_fail_ = ["CRASHED: " + (str(e_) or "AssertionError")], None
    ok = got_codes_ == want_codes_ and got_fail_ == want_fail_
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] #318 缺陷 1 {nm_} {lay_}:衝突碼 {got_codes_}(要 {want_codes_}),檢查失敗 {got_fail_}(要 {want_fail_})")
# (f) #319:C3 的承接帶要能跨房間的分塊。H6(退縫後的候選要補併料)的候選 3605:主支往高側貼到 [3600,3627],低側板邊的承接帶 [3596,3604] 靠併料 [3573,3600] 與主支 [3600,3627] 接住。
#     候選建構不放併料(突變 BC_no_doubling_cand 的效果,用 mut no_doubling)時,承接帶 [3596,3600] 沒有料:
#     板長沿 X 時承接帶沿 y,轉紅;板長沿 Y 時承接帶沿 x,x=3600 是房間的分塊邊界(頂點的 x 座標),承接帶一半在隔壁碎塊裡,以前 C3 只量縫所在的那一塊([3600,3604]),全過。
#     沒有突變時(有併料)候選要通過全部檢查(確認新的量法沒有誤報)。失敗的缺口要是 [3596,3600] 這 4 mm。
#     左右鏡像的轉置版(右上起鋪,縫 3720 − 3605 = 115;分塊邊界 x=120,主支被端面規則往低側推 9 mm 到 [93,120],高側板邊的承接帶 [116,124] 一半在分塊 [120,…] 裡):
#     這一個走的是 C3 的左邊(承接帶往 +x 走),上面兩個走右邊;缺口要是 [120,124]。鏡像時置中主支 [c−13, c+14] 差 1 mm,所以這一個只釘〈C3 沒有誤報、不放併料時缺口對〉。
for nm_, room_, lay_, seam_, gap_ix_, want_gap_ in (
        ("H6 板長沿 X", HAND_POCKET(3646, 3600), "左上起鋪,板長沿X", 3605, (1, 3), (3596, 3600)),
        ("H6 轉置(板長沿 Y)", TRANSPOSE(HAND_POCKET(3646, 3600)), "左上起鋪,板長沿Y", 3605, (0, 2), (3596, 3600)),
        ("H6 轉置再左右鏡像(右上起鋪)", MIRROR(TRANSPOSE(HAND_POCKET(3646, 3600)), 0), "右上起鋪,板長沿Y", 115, (0, 2), (120, 124))):
    r_ok_ = fo.build_candidate(room_, LAY[lay_], p, seam_)
    r_bad_ = fo.build_candidate(room_, LAY[lay_], p, seam_, frozenset({"no_doubling"}))
    f_ok_ = [f["check"] for f in fo.check(r_ok_, p, _cand=True)]
    f_bad_ = [f for f in fo.check(r_bad_, p, _cand=True) if f["check"] == "C3_EDGE_UNSUPPORTED"]
    gaps_ = {(f["gap"][gap_ix_[0]], f["gap"][gap_ix_[1]]) for f in f_bad_}
    ok = not r_ok_["conflicts"] and "C3_EDGE_UNSUPPORTED" not in f_ok_ and bool(f_bad_) and gaps_ == {want_gap_}
    if not nm_.endswith("(右上起鋪)"):
        ok = ok and not f_ok_  # 前兩個:有併料時整個候選要通過全部檢查
    failed |= not ok
    print(f"[{'綠' if ok else '錯!'}] #319 候選 {seam_} {nm_}:有併料時衝突 {sorted({c['code'] for c in r_ok_['conflicts']})}、檢查失敗 {sorted(set(f_ok_))}(C3 要沒有);"
          f"不放併料時 C3 缺口 {sorted(gaps_)}(要 [{want_gap_}],共 {len(f_bad_)} 處)")
# x_band 本身(手寫常數;rect = (x0, y0, x1, y1);cell 的碎塊 qs 在分塊邊界 x=120 切開,左邊 seg 在 x0=116 往 +x 走 8 mm,右邊 seg 在 x1=124 往 -x 走 8 mm):
#   (1) 隔壁碎塊 y 範圍相同:合成一個矩形跨過邊界;(2) 隔壁碎塊 y 範圍較窄:只留還連得上的 y 範圍,分成兩個矩形;
#   (3) 右邊走法與 (1) 對稱;(4) 隔壁中間有孔(y 40–60 沒有碎塊):孔那段不算,孔另一側的碎塊也只留自己的 y 範圍(從板邊一路連續過來才算);(5) 隔壁沒有碎塊(牆):和以前夾在碎塊裡的承接帶一樣;
#   (6) 隔壁碎塊比自己寬(y 0–100 對自己的 30–60):只留板邊那一段 30–60,不往兩邊擴(承接帶是從這一段板邊往板內量的)。
_xb_cases = (
    ("相同 y 範圍", [(116, 10, 120, 90), (120, 10, 300, 90)], (115, 10, 116, 90), 1, [(116, 10, 124, 90)]),
    ("隔壁較窄", [(116, 10, 120, 90), (120, 30, 300, 90)], (115, 10, 116, 90), 1, [(116, 10, 120, 90), (120, 30, 124, 90)]),
    ("右邊對稱", [(100, 10, 120, 90), (120, 10, 124, 90)], (124, 10, 125, 90), -1, [(116, 10, 124, 90)]),
    ("隔壁有孔", [(116, 0, 120, 100), (120, 0, 300, 40), (120, 60, 300, 100)], (115, 0, 116, 100), 1,
     [(116, 0, 120, 100), (120, 0, 124, 40), (120, 60, 124, 100)]),
    ("隔壁是牆", [(116, 10, 120, 90)], (115, 10, 116, 90), 1, [(116, 10, 120, 90)]),
    ("隔壁較寬", [(116, 30, 120, 60), (120, 0, 300, 100)], (115, 30, 116, 60), 1, [(116, 30, 124, 60)]))
_bad_xb = [(nm_, sorted(fo.x_band(qs_, seg_, d_, 8)), sorted(want_)) for nm_, qs_, seg_, d_, want_ in _xb_cases
           if sorted(fo.x_band(qs_, seg_, d_, 8)) != sorted(want_)]
ok = not _bad_xb
failed |= not ok
print(f"[{'綠' if ok else '錯!'}] #319 x_band(承接帶跨分塊)手寫案例 {len(_xb_cases)} 個:不一致 {_bad_xb}")
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
# P-182 第三版 C7 的裁決(#251 審查 718cc9a3、4e1f1161):對建構端的 candidate trace 動手腳,C7 都要抓到。
#   C7 不信 trace:候選集合與選擇規則自己算,每個候選自己重建(build_candidate)、跑完整 check(),和 trace 宣稱的可行與失敗碼逐一比對。
#   trace 不存佈局;偽造的 trace 即使塞一份假佈局(舊版 C7 只比對最後一條縫就信了),C7 也不看它。
import copy as _copy  # noqa: E402

_lx = next(l for l in fo.LAYOUTS if fo.layout_name(l) == "左上起鋪,板長沿X")
_base45 = fo.build(STEP45, _lx, p)
_baseds = fo.build(DSROOM(3649, 3597), _lx, p)
_basepil = fo.build(PIL2745, _lx, p)
_basedbl = fo.build(DBLCOL, _lx, p)
_pil_alt = fo.build_candidate(PIL2745, _lx, p, 2704)  # 手算:壁柱面 y=2745,⌊2745 − 40.5⌋ = 2704


def _tamper(base_, how):
    r_ = _copy.deepcopy(base_)
    r_ = how(r_) or r_
    return {f["check"] for f in fo.check(r_, p)}, {x[0] for x in fo.p182_trace_problems(r_, p)}


def _t_seam(r_):  # 主支縫改回 trace 判為失敗的原縫位
    r_["seams_a"] = r_["seams_a"][:-1] + [3659]


def _t_falsefail(r_):  # 左牆壁柱 y 2745:原縫位可行(選中的就是它),trace 卻標成失敗
    r_["p182"]["cands"][0]["ok"] = False


def _t_drop(r_):  # 雙牆階:拿掉 3608 那一筆
    r_["p182"]["cands"] = [e for e in r_["p182"]["cands"] if e["d"] != 3608]


def _t_noncand(r_):  # 選中一個不在候選集合裡的位置
    r_["seams_a"] = r_["seams_a"][:-1] + [3600]
    r_["p182"]["cands"].append(dict(_copy.copy(r_["p182"]["cands"][-1]), d=3600, seam=3600, ok=True))


def _t_codes(r_):  # 雙牆階:3608 確實不可行,但 trace 寫的失敗碼不是重建出來的那些
    for e in r_["p182"]["cands"]:
        if e["d"] == 3608:
            e["codes"], e["checks"] = ["MAIN_DOUBLING_BLOCKED"], ["C3_EDGE_UNSUPPORTED"]


def _t_skip(r_):  # 雙牆階:3608 標成可行卻沒選
    for e in r_["p182"]["cands"]:
        if e["d"] == 3608:
            e["ok"] = True


def _t_false_ok(r_):  # 雙牆階:把 3608 標成可行並選它(縫位也改成 3608),但 3608 重建後其實不可行
    for e in r_["p182"]["cands"]:
        if e["d"] == 3608:
            e["ok"], e["codes"], e["checks"] = True, [], []
    r_["p182"]["chosen"] = 3608
    r_["seams_a"] = r_["seams_a"][:-1] + [3608]


def _t_give_up_dbl(r_):  # 三個候選都不可行的房間:trace 只列原縫位就放棄(報 P182_NO_FEASIBLE_CANDIDATE 的樣子照舊)
    r_["p182"]["cands"] = r_["p182"]["cands"][:1]


def _t_extra_entry(r_):  # 雙牆階:trace 多列了一個不在候選集合裡的位置(3000),選中的 3556 照舊
    r_["p182"]["cands"].append(dict(d=3000, seam=3000, ok=False, codes=[], checks=[], why=""))


def _t_chosen_mismatch(r_):  # 左牆壁柱 y 2745:結果換成退到 2704 的佈局(它也可行),trace 卻說選的是原縫位 2750
    out = _copy.deepcopy(_pil_alt)
    out["p182"] = r_["p182"]
    return out


def _t_none_unflagged(r_):  # 三個候選都不可行的房間:trace 說沒有可行的,結果卻沒報 P182_NO_FEASIBLE_CANDIDATE(變成可施工)
    r_["conflicts"] = []


def _t_none_wrong_seam(r_):  # 同一間:報了 P182_NO_FEASIBLE_CANDIDATE,結果的縫位卻不是原縫位(選了第二個候選 3624)
    r_["seams_a"] = r_["seams_a"][:-1] + [3624]


def _t_give_up_ds(r_):  # 審查員 forge.py 的〈放棄〉:雙牆階 3649/3597 其實可行(3556),trace 只留原縫位 3659,冒充都不可行
    r_["p182"] = dict(r_["p182"], cands=r_["p182"]["cands"][:1], chosen=None)
    r_["conflicts"] = [dict(code="P182_NO_FEASIBLE_CANDIDATE", seam=3659)]
    r_["seams_a"] = r_["seams_a"][:-1] + [3659]


def _t_fake_layout(r_, change_seam=False):  # 審查員 forge.py 的〈偽造佈局〉:結果是退到 2704 的佈局;trace 說原縫位 2750 失敗,
    #   並附一份假佈局當證據(舊版 C7 只比對那份佈局的最後一條縫,就信了)。其實 2750 可行。
    #   (a) 假佈局是刪了併料的原縫位佈局;(b) 假佈局是換掉前面一條縫、最後一條縫仍是 2750 的佈局(change_seam=True)
    fake = _copy.deepcopy(_basepil)
    if change_seam:
        fake["seams_a"] = [fake["seams_a"][0] + 4] + fake["seams_a"][1:]
    else:
        fake["timbers"] = [t for t in fake["timbers"] if not t.get("doubling")]
    fake_old = dict(d=2750, seam=2750, ok=False, codes=[], checks=["C3_EDGE_UNSUPPORTED"], res=fake)
    out = dict(_copy.deepcopy(_pil_alt))
    out["p182"] = dict(c0=2750, d0=2750, chosen=2704, cands=[fake_old, dict(d=2704, seam=2704, ok=True, codes=[], checks=[], res=_pil_alt)])
    return out


def _t_fake_seam(r_):
    return _t_fake_layout(r_, change_seam=True)


for nm_, base_, how_, want_, why_ in (
        ("tamper_main_seam", _base45, _t_seam, "C7_P182_CHOSE_FAILED", "45 mm 牆階的主支縫改回 3659(trace 判它不可行)"),
        ("tamper_false_fail", _basepil, _t_falsefail, "C7_P182_FALSE_FAIL", "左牆壁柱 y 2745:trace 把可行的原縫位標成失敗"),
        ("tamper_trace_drop", _baseds, _t_drop, "C7_P182_TRACE_INCOMPLETE", "雙牆階 3649/3597:比選中的 3556 優先的 3608 不在 trace"),
        ("tamper_noncandidate", _base45, _t_noncand, "C7_P182_NOT_CANDIDATE", "選中 3600:不在 C7 自己算的候選集合"),
        ("tamper_skip_feasible", _baseds, _t_skip, ("C7_P182_SKIPPED_FEASIBLE", "C7_P182_FALSE_OK"), "trace 說 3608 可行,卻選了 3556"),
        ("tamper_codes", _baseds, _t_codes, "C7_P182_CODES_MISMATCH", "雙牆階 3608 確實不可行,但 trace 寫的失敗碼和 C7 重建出來的不同"),
        ("tamper_false_ok", _baseds, _t_false_ok, ("C7_P182_FALSE_OK", "C7_P182_CHOSE_FAILED"), "trace 說 3608 可行並選它,C7 重建後 3608 其實不可行"),
        ("tamper_give_up", _basedbl, _t_give_up_dbl, "C7_P182_TRACE_INCOMPLETE", "三個候選都不可行(3667、3624、3579)的房間:trace 只列原縫位就放棄,C7 要求涵蓋全部候選"),
        ("tamper_chosen_mismatch", _basepil, _t_chosen_mismatch, "C7_P182_CHOSE_FAILED", "結果是另一個可行的候選 2704,trace 說選的是原縫位 2750"),
        ("tamper_extra_entry", _baseds, _t_extra_entry, "C7_P182_NOT_CANDIDATE", "trace 多列了一個不在 C7 候選集合裡的位置 3000(選中的 3556 沒動)"),
        ("tamper_none_unflagged", _basedbl, _t_none_unflagged, "C7_P182_CHOSE_FAILED", "都不可行的房間:trace 說沒有可行的候選,結果卻沒報 P182_NO_FEASIBLE_CANDIDATE"),
        ("tamper_none_seam", _basedbl, _t_none_wrong_seam, "C7_P182_CHOSE_FAILED", "都不可行的房間:報了 P182_NO_FEASIBLE_CANDIDATE,結果的縫位卻不是原縫位"),
        ("tamper_give_up_ds", _baseds, _t_give_up_ds, ("C7_P182_TRACE_INCOMPLETE", "C7_P182_SKIPPED_FEASIBLE"), "審查員 forge.py 的放棄:雙牆階 3649/3597 其實可行,trace 只留原縫位就報都不可行"),
        ("tamper_fake_seam", _basepil, _t_fake_seam, ("C7_P182_FALSE_FAIL", "C7_P182_SKIPPED_FEASIBLE"), "審查員 forge.py 的偽造佈局(b):假佈局換掉前面一條縫、最後一條縫仍是 2750;C7 不看存的佈局"),
        ("tamper_fake_layout", _basepil, _t_fake_layout, ("C7_P182_FALSE_FAIL", "C7_P182_SKIPPED_FEASIBLE"), "審查員 forge.py 的偽造佈局:原縫位 2750 其實可行,trace 附一份刪了併料的假佈局說它失敗;C7 不看存的佈局")):
    got_, probs_ = _tamper(base_, how_)
    wants_ = (want_,) if isinstance(want_, str) else want_  # 預期碼可以是一組:每一個都要報(一個碼報了不代表另一條規則也在)
    ok = all(w_ in got_ and w_ in probs_ for w_ in wants_)  # check() 與直接呼叫 p182_trace_problems(掃描對不可施工的結果用這個)都要抓到
    failed |= not ok
    print(f"[{'紅' if ok else '沒抓到!'}] {nm_:18s} 預期 {'+'.join(wants_):24s} 實得 {sorted(x for x in got_ if x.startswith('C7_P182'))}  {why_}")
# 衝突碼在檢查端沒有對應的檢查(C7_P182_FAIL_UNCONFIRMED):把 check() 對候選的檢查換成永遠全過(模擬檢查端有盲點),
#   雙牆階 3649/3597 的原縫位 3659 重建後有衝突碼、檢查全過,要標出來(不是默默當成失敗)
_orig_check = fo.check
fo.check = lambda res_, p_, _cand=False: [] if _cand else _orig_check(res_, p_, _cand)
try:
    _probs = fo.p182_trace_problems(_baseds, p)
finally:
    fo.check = _orig_check
ok = "C7_P182_FAIL_UNCONFIRMED" in {x[0] for x in _probs}
failed |= not ok
print(f"[{'紅' if ok else '沒抓到!'}] tamper_blind_check  預期 C7_P182_FAIL_UNCONFIRMED  實得 {sorted({x[0] for x in _probs})}  C7 重建的候選有衝突碼、檢查全過(檢查端盲點)")
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


def expected_for_scan(expected_fam, ids_scan, ci):
    """掃描斷言要比對的預期清單(一族)。CI 模式只掃抽樣的房間,預期清單也只取這些房間的部分(鏡像的 id 是 房間|上下 或 房間|左右);
    --quick、--full 掃全部房間,預期清單整份逐筆比對:產生器少掃了哪一間房,那間房的不可施工排法就會報〈少了〉
    (#251 審查 92e64028:原本任何模式都拿〈這次掃到的房間〉過濾預期清單,產生器漏掉一間房,過濾後預期清單跟著少,漏掉的房間就不會被發現)。"""
    return {(r_, l_, tuple(c_)) for r_, l_, c_ in expected_fam if not ci or r_.split("|")[0] in ids_scan}


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
# 產生器漏掉一間房(#251 審查 92e64028):--quick、--full 的預期清單整份逐筆比對,漏掉的房間要報〈少了〉;只有 CI 才取〈這次掃到的房間〉
_fe = [("A", "左上起鋪,板長沿Y", ["C1"]), ("B|上下", "左下起鋪,板長沿X", ["C2"]), ("B|左右", "右下起鋪,板長沿X", ["C2"])]
_got_a = {("A", "左上起鋪,板長沿Y", ("C1",))}  # 實得只有房間 A:產生器漏掉了房間 B
_x_all, _m_all = compare_unbuildable(_got_a, expected_for_scan(_fe, {"A"}, False))
_x_ci, _m_ci = compare_unbuildable(_got_a, expected_for_scan(_fe, {"A"}, True))
ok = not _x_all and _m_all == [("B|上下", "左下起鋪,板長沿X", ("C2",)), ("B|左右", "右下起鋪,板長沿X", ("C2",))] and not _x_ci and not _m_ci
failed |= not ok
print(f"[{'紅' if ok else '沒抓到!'}] expected_for_scan  預期 --quick/--full 報少了漏掉的房間、CI 只比對掃到的房間:非 CI 少了 {len(_m_all)} 筆(要 2)、CI 少了 {len(_m_ci)} 筆(要 0)")


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


def _tick(label):
    print(f"[計時] {label}:累計 {time.time() - t0:.0f} 秒", flush=True)


bad = []
layouts = fo.LAYOUTS if FULL else [LT_Y]
cases = [(W, 2500) for W in range(300, 4001)] + [(2000, H) for H in range(300, 6001)]
if CI:
    cases = cases[::CI_SAMPLE["rect1d"]]  # 取每第 k 個尺寸(決定性)
runs = 0
for W, H in cases:
    for l in layouts:
        runs += 1
        res = fo.build(RECT(W, H), l, p)
        fails = [] if res["conflicts"] else fo.check(res, p)
        if res["conflicts"] or fails:
            bad.append((W, H, fo.layout_name(l), sorted({c["code"] for c in res["conflicts"]}), sorted({f["check"] for f in fails})))
_tick("矩形房一維逐 mm 掃描")
band = range(-45, 46) if FULL else CI_SAMPLE["band"] if CI else (-43, -42, -41, -40, -39, -1, 0, 1, 2)
_gw, _gh = (97, 211) if FULL else (CI_SAMPLE["grid_w"], CI_SAMPLE["grid_h"]) if CI else (331, 617)
edge_w = sorted({k * 917 + d for k in range(1, 5) for d in band if 300 <= k * 917 + d <= 4000}
                | set(range(300, 4001, _gw)))
edge_h = sorted({k * 1832 + d for k in range(1, 4) for d in band if 300 <= k * 1832 + d <= 6000}
                | set(range(300, 6001, _gh)))
for W in edge_w:
    for H in edge_h:
        for l in fo.LAYOUTS:
            runs += 1
            res = fo.build(RECT(W, H), l, p)
            fails = [] if res["conflicts"] else fo.check(res, p)
            if res["conflicts"] or fails:
                bad.append((W, H, fo.layout_name(l), sorted({c["code"] for c in res["conflicts"]}), sorted({f["check"] for f in fails})))
_tick("矩形房二維掃描")
# 凹角房:L 形(缺一角)與壁龕(牆上內凹),8 種排法;可施工的排法都要通過全部檢查(含 C8 核心可表示)
LROOM = lambda W, H, cw, ch: {"outer": [[0, 0], [W, 0], [W, H - ch], [W - cw, H - ch], [W - cw, H], [0, H]]}
ALCOVE = lambda W, H, y0, y1, dep: {"outer": [[dep, 0], [W, 0], [W, H], [dep, H], [dep, y1], [0, y1], [0, y0], [dep, y0]]}
reflex_rooms = [(f"L:{W},{H},{cw},{ch}", LROOM(W, H, cw, ch)) for W in (3000, 4100, 5000) for H in (2600, 3700, 4800)
                for cw in range(300, W - 299, 457) for ch in range(300, H - 299, 613)]
reflex_rooms += [(f"A:{W},{y0},{L},{dep}", ALCOVE(W, 3000, y0, y0 + L, dep)) for W in (3000, 4400) for y0 in (400, 1000, 1700)
                 for L in (400, 900) for dep in (300, 600) if y0 + L <= 2600]
reflex_rooms += [(f"C:{W},{H},{x},{y},{cs}", COLUMN(W, H, x, y, cs)) for W, H in ((3600, 3000), (5000, 4200)) for cs in (300, 450)
                 for x in range(500, W - cs - 499, 433) for y in range(500, H - cs - 499, 521)]
if CI:
    reflex_rooms = reflex_rooms[::CI_SAMPLE["reflex"]]  # 取每第 k 間(決定性)
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
_tick("凹角、壁龕與獨立柱房")
# 牆階 1–100 mm:L 形缺角很淺(橫向或縱向)與很淺的壁龕,8 種排法。可施工的排法都要通過全部檢查。
#   (#251 審查 60785906:牆階 13–24 mm 時沿牆料端面頂延伸段,原本沒宣告 custom 3,C8_I19_PRIORITY 會紅。)
step_rooms = ([(f"L_ch:{s}", LROOM(4100, 3700, 1500, s)) for s in range(1, 101)] + [(f"L_cw:{s}", LROOM(4100, 3700, s, 1200)) for s in range(1, 101)]
              + [(f"alcove:{s}", ALCOVE(4100, 3000, 1000, 1900, s)) for s in range(1, 101)]
              # 雙牆階(#251 審查 98cb7da0):牆 y=s1(x 2600–3300)、y=s2(x 3300–4100),s2 < s1
              + [(f"DS:{s1},{s2}", {"outer": [[0, 0], [4100, 0], [4100, s2], [3300, s2], [3300, s1], [2600, s1], [2600, 3700], [0, 3700]]})
                 for s1 in range(3604, 3700, 9) for s2 in range(s1 - 88, s1, 9)])
if CI:
    step_rooms = step_rooms[::CI_SAMPLE["step"]]  # 取每第 k 間(決定性);鏡像用同一批,所以鏡像也是抽樣
unb["step"], sbuild, _sb, scodes, _n = sweep_family(step_rooms)
runs += _n
sbad = len(_sb)
rb += _sb
print(f"牆階 1–100 mm 的 L 形、壁龕與雙牆階 {len(step_rooms)} 間 × 8 種排法:可施工 {sbuild} 個,其中檢查失敗 {sbad} 個;"
      f"不可施工的排法數(依原因){scodes}")
_tick("牆階與雙牆階")
# 鏡像:同一批房間上下、左右各翻一次。⌊w/2⌋ 與 ⌈w/2⌉ 不對稱,反向起鋪那半邊(back = ⌈w/2⌉)原本只有鏡像房才測得到。
unb["step_mirror"], mbuild, _mb, mcodes, _n = sweep_family(step_rooms, mirror=True)
runs += _n
mbad = len(_mb)
rb += _mb
print(f"鏡像(上下、左右)的牆階與雙牆階 {2 * len(step_rooms)} 間 × 8 種排法:可施工 {mbuild} 個,其中檢查失敗 {mbad} 個;"
      f"不可施工的排法數(依原因){mcodes}")
_tick("牆階與雙牆階的鏡像")
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


_stp = 1 if FULL else CI_SAMPLE["p182"] if CI else 3
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
if CI:
    _fam["t14 壁柱加柱"] = _fam["t14 壁柱加柱"][::CI_SAMPLE["t14"]]
for _nm, _rooms in _fam.items():
    _n, _nb, _nu, _bad, _k11 = _p182_family(_nm, _rooms, mirror_pairs=_nm.startswith("t10"))
    runs += _n
    ok = not _bad
    failed |= not ok
    _mir = _nm.startswith("t10")  # 只有分辨房族跑了上下鏡像比對;其他族不印〈鏡像不對稱 0〉,免得像是驗過
    print(f"[{'綠' if ok else '錯!'}] P-182 候選掃描 {_nm}:{_n} 次,可施工 {_nb}、不可施工 {_nu};"
          f"{'檢查失敗、trace 被 C7 判有問題、鏡像不對稱' if _mir else '檢查失敗、trace 被 C7 判有問題(這一族沒跑鏡像)'} {len(_bad)}"
          f"(已知缺陷 C11_MAIN_NOT_BUTTED {_k11} 次,另開工單)")
    for x in _bad[:8]:
        print("    ", x)
_tick("P-182 候選四族")
# 不可施工的排法要和明列的預期清單(每筆附原因代碼)完全一樣;清單空的就要 0 個。--write-expected 只在人工覆核後重寫清單。
if "--write-expected" in sys.argv:
    json.dump({fam: sorted([list(x[:2]) + [list(x[2])] for x in v]) for fam, v in unb.items()}, open(EXP_PATH, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=0)
expected_unb = json.load(open(EXP_PATH, encoding="utf-8"))
_ids_scan = {"reflex": {r_ for r_, _ in reflex_rooms}, "step": {r_ for r_, _ in step_rooms}, "step_mirror": {r_ for r_, _ in step_rooms}}
for fam in ("reflex", "step", "step_mirror"):
    # CI 模式只掃抽樣的房間:預期清單也只取這些房間的部分;--quick、--full 整份逐筆比對(expected_for_scan)
    want_ = expected_for_scan(expected_unb[fam], _ids_scan[fam], CI)
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
    for W in range(1200, 4001, 233 * (CI_SAMPLE["odd"] if CI else 1)):
        for H in range(1900, 5001, 377 * (CI_SAMPLE["odd"] if CI else 1)):
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
_tick("奇數縫寬與收尾")
print(f"掃描 {runs} 次建構({'完整' if FULL else '快速' if QUICK else 'CI 抽樣'}),{time.time() - t0:.0f} 秒;不可施工或檢查失敗 {len(bad)} 個")
for b in bad[:30]:
    print("   ", b)
failed |= bool(bad)
sys.exit(1 if failed else 0)
