# #318、#319 補丁的測試計畫(草稿,這一輪沒有執行任何一項)

- 補丁:`patch.diff`(對 `origin/main` = `adbaebf9`;用暫時索引 `git read-tree origin/main` + `git apply --cached --check` 驗過,通過;沒有動工作樹)。
- 新測試全部在 `selftest.py`(`--mutants-only` 與 `--ci` 都會跑),新增的手寫常數都附推導,**期望值不從程式讀回**。
- 約定:`[綠]`/`[錯!]` 是 selftest 的輸出前綴;下面〈舊〉= `origin/main` 的 `framing_oracle.py`,〈新〉= 套補丁後。

## 1. 新增測試一覽

| ID | 位置 | 斷言 | 舊程式 | 新程式(預期) |
|---|---|---|---|---|
| T-A1 | selftest 區塊 (a) | `Region.inside` 在牆線上的 12 個探測點(L 形 `LROOM(3600,3000,1800,1000)` 8 個、STEP45+孔 4 個),室內/室外手寫 | 8 個當掉(`AssertionError`,印成 `CRASHED`)、4 個走舊路徑對 | 12 個全對 |
| T-A2 | 區塊 (b) | 三間 L 形房 × 8 種排法:`seams_a`、`seams_b`、衝突碼 `[]`、檢查失敗 `[]`(手推常數,§2) | 24 個全當掉(issue 觀察) | 24 個全綠 |
| T-A3 | 區塊 (b) 後半 | 同三間的上下鏡像、左右鏡像、轉置 × 8 種排法:衝突碼 `[]`、檢查失敗 `[]` | 上下/左右鏡像每間 16 個當掉;轉置不當(切線永遠垂直,崩潰有方向性) | 72 個全綠 |
| T-A4 | 區塊 (c) | issue 第二個最小重現:STEP45+孔 x 2500–2700 y 500–800 與孔 x 2400–2800 y 1000–1300,各 8 種排法:不當掉;可施工的檢查全過;不可施工的 trace 沒問題 | 當掉 | 綠(不釘縫位) |
| T-A5 | 區塊 (d) | 缺角寬 = 房寬一半的 L 形 27 間 × 8 = 216 個排法:不當掉、可施工的檢查全過;印出不可施工數(預期 0) | 當掉 | 綠 |
| T-B1 | 區塊 (e) | `COLSTEP(3000)`、`COLSTEP(2900)` 左上 X ⇒ 衝突碼恰為 `[CORE_LIMIT_BOUNDARY_END_FREE]`;`COLSTEP(3100)` ⇒ 可施工且檢查全過;`MIRROR(COLSTEP(3000), 0)` 右上 X ⇒ 同上 | `COLSTEP(3000)`、`COLSTEP(2900)`、鏡像:衝突碼 `[]`(可施工)而 check 紅;`COLSTEP(3100)` 綠 | 全綠 |
| T-B2 | `MUTANTS` 4 筆 | `no_boundary_end_scan`(旗標拿掉新判定)套在 `COLSTEP(3000)` 要被 C8_I19_BOUNDARY_END、C3、C6 抓到;`COLSTEP(2900)` 要被 C8_I19_BOUNDARY_END 抓到 | 舊程式不認這個旗標 = 舊行為,4 筆本來就紅(綠燈) | 4 筆 `[紅]` |
| T-C1 | 區塊 (f) | H6 候選(`build_candidate`,縫 3605)有併料:不報衝突、C3 沒有、(前兩個)全部檢查沒有;不放併料(`mut={"no_doubling"}`)時 C3 缺口恰為 [3596,3600](板長沿 X 看 y、轉置版看 x);第三個是轉置再左右鏡像、右上起鋪、縫 115,缺口 [120,124](走 C3 的左邊) | 板長沿 X 綠;轉置版、鏡像版紅(C3 全過,缺口集合為空) | 3 個全綠 |
| T-C2 | 區塊 (f) 後 | `x_band` 7 個手寫案例(同 y 範圍合成一個矩形、隔壁較窄、右邊對稱、隔壁有孔、隔壁是牆、隔壁較寬) | `AttributeError`(沒有這個函式)⇒ selftest 當掉 | 綠 |
| T-D | `tp_scan.py`(不在補丁裡) | 房間 R 用排法 l 與轉置房間 T(R) 用轉置排法 T(l) 的結果完全相同 | — | 預期 0 不一致,有就是隱藏缺陷的證據 |

既有測試受影響的點(要在實跑時看):TR182(16 間 × 4 種排法 = 64 個,轉置族)現在跑的是較嚴的 C3,這就是 #319 要求的〈掃一遍現有的轉置族〉;其餘既有斷言預期不變。

## 2. 手推常數與推導(T-A2),供交叉確認

規則:`P=915, L=1830, gap=2, w=27, X=8, M=367, min_piece=27`(`rooms.json`)。主支縫(沿 A 軸)中心距起鋪牆:`916, 1833, 2750, 3667, 4584`(= 917k + 916,只要 917(k+1) < 深度);板端縫(沿 B 軸):`1831, 3663`(= 1832k + 1831,只要 1832(k+1) < 深度)。G7:最後一條縫離〈縫線上最近的對牆〉不到 40.5 才挪。
`LROOM(W,H,cw,ch)` = `[[0,0],[W,0],[W,H−ch],[W−cw,H−ch],[W−cw,H],[0,H]]`,缺角在 (+x,+y);縫線上最近的對牆:從 min 側起鋪時,縫線在缺角下緣 `y=H−ch`(或垂直牆 `x=W−cw`)之前,對牆是缺角牆;之後是房的外框。從 max 側起鋪的對牆(x=0、y=0)是平的。

| 房間 | 深度(y / x) | yP min | yP max | xL min | xL max | xP min | xP max | yL min | yL max |
|---|---|---|---|---|---|---|---|---|---|
| 3600×3000 缺 1800×1000(缺角牆 y=2000、x=1800) | 3000 / 3600 | 916,1833,2750 | 250,1167,2084 | 1831 | 1769 | 916,1833,2750 | 850,1767,2684 | 1831 | 1169 |
| 4000×3000 缺 2000×1000(y=2000、x=2000) | 3000 / 4000 | 916,1833,2750 | 250,1167,2084 | 1831,3663 | 337,2169 | 916,1833,2750,3667 | 333,1250,2167,3084 | 1831 | 1169 |
| 5000×4000 缺 2500×1600(y=2400、x=2500) | 4000 / 5000 | 916,1833,2750,3667 | 333,1250,2167,3084 | 1831,3663 | 1337,3169 | 916,1833,2750,3667,4584 | 416,1333,2250,3167,4084 | 1831,3663 | 337,2169 |

排法對應:`yP` = 板長沿 X 的主支縫(沿 y)、`xL` = 板長沿 X 的板端縫(沿 x)、`xP` = 板長沿 Y 的主支縫(沿 x)、`yL` = 板長沿 Y 的板端縫(沿 y)。
左上X = (yP min, xL min);右上X = (yP min, xL max);左下X = (yP max, xL min);右下X = (yP max, xL max);左上Y = (xP min, yL min);左下Y = (xP min, yL max);右上Y = (xP max, yL min);右下Y = (xP max, yL max)。(`layout_name` 的第一字是 x 方向、第二字是 y 方向;A 軸 = 板寬方向 = 主支之間。)

G7 逐條確認(沒有一條需要挪):
- 3600×3000:yP min 最後 2750,縫線 y=2749.5 > 缺角下緣 2000,只穿過 x<1800 那段,對牆 y=3000,2750 ≤ 2959.5;xL min 1831,縫線 x=1830.5 > 1800,對牆 x=3600;xP min 最後 2750,對牆 x=3600;yL min 1831,縫線 y=1830.5 < 2000,對牆 = 缺角下緣 2000,1831 ≤ 1959.5(離對牆 169,全部縫位離對牆最近的)。
- 4000×3000:xL 3663、xP 3667 對牆 x=4000(縫線在缺角垂直牆 x=2000 之後),≤ 3959.5。
- 5000×4000:yP 3667 對牆 4000、yL 3663 對牆 4000,≤ 3959.5;xL 3663、xP 4584 對牆 5000,≤ 4959.5。
- 從 max 側起鋪:對牆是平的,最近 250(yP/xP 的 250 與 333)。

P-182:最後一條主支縫離與它平行的牆都 ≥ 250 mm,主支寬度只有縫兩側各 14 mm ⇒ 沒有擋料 ⇒ 沒有候選、沒有 trace。

**我預期這 24 個排法全部可施工、檢查全過**。依據:(1) 這三間在原 L 形掃描(579 間 × 8 種排法,不可施工 0 個)的同一族,(2) 唯一特別的是 W/2 讓下緣水平邊中點落在凹角牆線上,新 `inside` 對它給出與一般情形相同的答案。這個預期是類推,沒有實跑。最可能不同的一個:3600×3000 右上/右下起鋪板長沿 Y(`xP max`,縫 x = 1767 離缺角牆 x=1800 只有 33 mm,主支被推 8 mm 補併料);若這一個出現衝突或檢查失敗,**先照物理判斷是手推錯(縫位、併料)還是程式缺陷,不要把期望值改成程式輸出**。

## 3. 原始碼突變(會讓修法轉紅)

格式同 `framing-oracle-gaps/round21/run9.py` 的 `MUTS`(`(old, new)` 要在 `framing_oracle.py` 裡恰好出現一次;補丁沒有動任何既有突變的字串,新字串我用 `grep -c` 查過各出現 1 次,`bad or free` 那行在 `check()` 裡也有同一行,所以用兩行錨點)。`NL = "\n"`。

```python
# ---- 第 22 輪(#318、#319)
MUTS["F2a_inside_no_wallline_branch"] = ("        if x not in self.coords[0]:", "        if True:")
MUTS["F2b_inside_wallline_inverted"] = ("        return iv_find(self.section(1, y), x) is not None", "        return iv_find(self.section(1, y), x) is None")
MUTS["F1a_boundary_end_scan_off"] = ('    if not conflicts and "no_boundary_end_scan" not in mut:', "    if False:")
MUTS["F1b_boundary_end_free_only_dropped"] = ("            if bad or free:" + NL + "                fb = rng((free or indoor)[0], b)",
                                              "            if bad:" + NL + "                fb = rng((free or indoor)[0], b)")
MUTS["F1c_boundary_end_flags_extension"] = ("            if (at == lo and lo < pe[0]) or (at == hi and hi > pe[1]):" + NL + "                continue  # 超出定位邊的延伸段端面",
                                            "            if False:" + NL + "                continue  # 超出定位邊的延伸段端面")
MUTS["F1d_boundary_end_even_if_conflicts"] = ('    if not conflicts and "no_boundary_end_scan" not in mut:', '    if "no_boundary_end_scan" not in mut:')
MUTS["F3a_c3_left_clipped"] = ("((x0 - 1, y0, x0, y1), lambda s: x_band(qs, s, 1, X), 1),",
                               "((x0 - 1, y0, x0, y1), lambda s: [(x0, s[1], min(x0 + X, x1), s[3])], 1),")
MUTS["F3b_c3_right_clipped"] = ("((x1, y0, x1 + 1, y1), lambda s: x_band(qs, s, -1, X), 1),",
                                "((x1, y0, x1 + 1, y1), lambda s: [(max(x1 - X, x0), s[1], x1, s[3])], 1),")
MUTS["F3c_c3_both_clipped"] = [MUTS["F3a_c3_left_clipped"], MUTS["F3b_c3_right_clipped"]]
MUTS["F3d_xband_no_piece_clip"] = ("        ys = iv_intersect(ys, iv_norm([(r_[1], r_[3]) for r_ in qs if r_[0] < xm < r_[2]]))", "        pass")
MUTS["F3e_xband_no_connect"] = ("        ys = iv_intersect(ys, iv_norm([(r_[1], r_[3]) for r_ in qs if r_[0] < xm < r_[2]]))",
                                "        ys = iv_norm([(r_[1], r_[3]) for r_ in qs if r_[0] < xm < r_[2]])")
MUTS["F3f_xband_no_merge"] = ("        if merged and merged[-1][1] == r_[1] and merged[-1][3] == r_[3] and merged[-1][2] == r_[0]:", "        if False:")
MUTS["F3g_xband_no_cross"] = ("{v for r_ in qs for v in (r_[0], r_[2]) if lo < v < hi}", "set()")
```

注意 `MUTS` 的值是單一 `(old, new)` 或 `[(old, new), ...]`(同時改多處);`F3c` 用 list。

| 突變 | 預期轉紅的行 | 說明 |
|---|---|---|
| F2a | T-A1(8 個當掉)、T-A2(24 個當掉)、T-A3、T-A4、T-A5、既有 `P-182 手算 H*` 不受影響(沒有探測點在牆線上) | 舊行為 |
| F2b | T-A1(牆線上的點全反)、T-A2、T-A3(邊界材貼錯側 ⇒ `TIMBER_INTO_RC`/碰撞) | 牆線上取反 |
| F1a | T-B1 三個(報衝突沒了:可施工、check 紅) | 新判定拿掉 |
| F1b | T-B1 三個(`bad or free` 只剩 `bad`:`COLSTEP` 的 SB 端面是 `free`,不是 `bad`) | 只剩 `free` 條件的另一半 |
| F1c | 凹角延伸的端面被當成端面頂不到 ⇒ F1/F2 等有延伸的房間變不可施工:標準答案逐支比對、凹角掃描、`對照 …` 多行轉紅 | 延伸段略過條件拿掉 |
| F1d | **預期存活或轉紅都有可能**:只會把 `CORE_LIMIT_BOUNDARY_END_FREE` 加進〈已經有別的衝突〉的房間;`STEP20`、`DBLCOL` 轉置右起鋪等釘衝突碼清單的斷言若恰好有這個條件才會轉紅。實跑看。若存活,補一個釘〈已有衝突時衝突碼不變〉的對照(建議用 `DBLCOL` 轉置右起鋪的 `["TIMBERS_COLLIDE"]`,已在 TR182 裡) | 判定順序 |
| F3a | T-C1 第三個(左右鏡像轉置版:走左邊) | 只回到舊的左邊夾法 |
| F3b | T-C1 第二個(轉置版:走右邊) | 只回到舊的右邊夾法 |
| F3c | T-C1 第二、第三個;`BC_no_doubling_cand` 轉置版不再被 C3 抓到(= 補丁前的狀態) | 兩邊都回到舊行為 |
| F3d | T-C2〈隔壁是牆〉〈隔壁有孔〉 | 承接帶不被碎塊範圍限制 |
| F3e | T-C2〈隔壁較寬〉 | 沒有射線連通 |
| F3f | T-C2〈同 y 範圍〉〈右邊對稱〉〈隔壁較寬〉 | 沒有合併 |
| F3g | T-C1 第二、第三個(跨不過去 ⇒ 缺口集合為空;第一個板長沿 X 的上下邊不經 `x_band`,不受影響)、T-C2 的跨界案例 | 停靠點不含碎塊邊界 |

既有 122 處突變(`run9.py`):補丁沒有動它們的錨點,預期仍是 121 處紅、T2 等價存活;`BC_no_doubling_cand` 多出 T-C1 的紅行(它讓 `build_candidate` 對非原縫位的候選不放併料 ⇒ T-C1 的〈有併料時檢查全過〉那一項轉紅)。

## 4. 實跑順序(WSL 空下來之後;Windows 單獨跑,不要和正式驗收並行)

```
cd geometry-core/framing-template/oracle
# 4.1 先紅後綠(確認新測試真的有牙):只套 selftest.py 與 README,不套 framing_oracle.py
git apply --include='*/selftest.py' --include='*/README.md' ../../../drafts/oracle-318-319/patch.diff   # (路徑依實際位置調整)
python selftest.py --mutants-only    # 預期 exit 1;紅的行:T-A1、T-A2 ×3、T-A3 ×3、T-A4 ×2、T-A5、T-B1(柱右面/跨過/鏡像)3 行、T-C1 轉置與鏡像 2 行;
                                     # T-C2 那行是 AttributeError 當掉(舊程式沒有 x_band),不是 [錯!]
# 4.2 再套 framing_oracle.py
git apply --include='*/framing_oracle.py' ...
python selftest.py --mutants-only    # 預期 exit 0;新增行全綠
python selftest.py                   # --ci,預期 exit 0,秒數 ≤ 300(舊 205–210 + 新增約 10–25 的估計)
python selftest.py --quick           # 預期 exit 0;印出的不可施工數:step 528、step_mirror 1056、reflex 0;新紅燈 = 隱藏缺陷,見 §5
# 4.3 golden 與清單
python make_golden.py rooms.json /tmp/golden-new.json   # sha256 要等於 oracle-golden.json(165c2417…)
# 不可施工清單不用另外重寫:--quick 的輸出已逐筆比對 sweep-expected-unbuildable.json(reflex 0=0、step 528=528、step_mirror 1056=1056),
# 不要跑 --write-expected(它會直接覆寫清單檔)
# 4.4 原始碼突變
python <run9.py> <oracle 目錄> <輸出目錄> F2a_inside_no_wallline_branch F2b_inside_wallline_inverted F1a_boundary_end_scan_off F1b_boundary_end_free_only_dropped F1c_boundary_end_flags_extension F1d_boundary_end_even_if_conflicts F3a_c3_left_clipped F3b_c3_right_clipped F3c_c3_both_clipped F3d_xband_no_piece_clip F3e_xband_no_connect F3f_xband_no_merge F3g_xband_no_cross BC_no_doubling_cand BC_ax0
# 4.5 轉置對稱掃描(#319 第三項)
ORACLE_DIR=$PWD python ../../../drafts/oracle-318-319/tp_scan.py            # 抽樣
ORACLE_DIR=$PWD python ../../../drafts/oracle-318-319/tp_scan.py --quick    # 全部凹角/牆階房
# 4.6 審查員的 fz20.py(種子 1–4 各 150 間):buildcrash 欄預期 96/144/192/24 → 0;
#     〈可施工卻檢查失敗〉110 次中含 C8_I19_BOUNDARY_END 的 72 次 → 0(改成不可施工,CORE_LIMIT_BOUNDARY_END_FREE),其餘 38 次不變
```

### 4.7 〈BC_no_doubling_cand 在轉置版也要被 C3 抓到〉的人工驗證
1. 在 `selftest.py` 暫時把 `TR182_DBL = {"H6": [(3573, 3600)], "PIL2745": [(2718, 2745)]}` 的 `"H6"` 那筆拿掉(轉置版的併料不再被手釘)。
2. 套原始碼突變 `BC_no_doubling_cand`,跑 `python selftest.py --mutants-only`。
3. 預期紅,而且紅的行包含 TR182 的 `H6` 轉置版(候選 3605 因 C3 紅 ⇒ 不可行,縫位或 trace 與手寫常數不同)。補丁前:此步驟 `H6` 轉置版**全綠**(issue 觀察)。
4. 還原 `TR182_DBL`(它是第二道防線,保留)。

## 5. 紅燈時怎麼判讀(不要把期望值改成程式輸出)

- **T-A1/T-A2/T-A3/T-A5 紅**:先看是 `CRASHED`(→ `inside` 或另一個沒盤到的切線呼叫點,把 traceback 的 `section` 呼叫者貼出來)、縫位不符(→ 先重算 §2 的表,手推對就是 G7 或縫位程式的缺陷)、衝突碼非空(→ 把 `conflicts` 全文貼出,按物理判斷:放不下就是真的不可施工,要回頭改 §2 的預期並寫明物理原因;不是遷就輸出)。
- **T-B1 紅**:(a) 衝突碼不是恰好一個 → 看是否有別的衝突先出現(此時新判定被略過,屬預期的順序);(b) `COLSTEP(3100)` 紅 → 新判定在綠燈房間誤報,**是補丁的缺陷**,優先處理。
- **T-C1 紅**:缺口不是 [3596,3600] / [120,124] → 先看缺口實際範圍;鏡像版若檢查另有失敗(不是 C3),T-C1 第三項只要求 C3 沒有,不會因此紅。
- **新的掃描紅燈(--quick/--full 才看得到)**:C3 變嚴只多驗不少驗,所以紅燈是真的隱藏缺陷,不是誤報,**除非**能指出紅燈處承接帶的某一段其實在板外或被孔隔開(那就是 `x_band` 的射線連通寫錯)。處理:先判病因(物理缺口?建構端缺陷?),再決定是否修建構端/開工單;同 #318 的程序,不直接改 `sweep-expected-unbuildable.json`。
- **P-182 的 trace 變了**:`C7_P182_*` 一類碼,代表某個候選在較嚴的 C3 下由可行變不可行,先看是否 #319 的隱藏缺陷。

## 6. 這次沒有覆蓋的
- `boundary_end_conflicts` 的 `bad` 分支(端面壓到非 boundary 的料)沒有對照房:`COLSTEP` 觸發的是 `free` 分支。可以用突變 `rc_through_reflex`(F1)造出一個,但它在原本的 MUTANTS 迴圈走 `skip_conflict_scan`,要另寫斷言。
- 缺陷 1 的另外 38 次(`C8_I19_PRIORITY`、C11、C5_MAIN_GAP 等)。
- 孔邊上不在 `comp` 裡的部分(`COLSTEP(2900)` 的 x 2873–3000)沒有獨立的建構端衝突判定(現在是靠 SB 端面那一款一併抓到,如果沒有牆階垂直牆,同樣的窄縫會走 `RC_FACE_STRIP_OUTSIDE`)。若之後出現〈孔邊窄縫部分被略過、沒有 SB 端面問題〉的房型,會是漏報。
- 語法:所有新程式我只用眼睛核對,沒有跑直譯器;實跑第一件事是 `python -m py_compile framing_oracle.py selftest.py`。
