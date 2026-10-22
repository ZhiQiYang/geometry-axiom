# 第 22 輪 final head（審查 6332818768）

這份說明是 PR 正文。分支 `fix/framing-oracle-review-20261020`，base 是 `main`（`adbaebf9c73ea6801d7b4d5214e4b846b132923b`）。審查對象是該分支在 `1126991c9dbd3de92d8cce6eab2419f8f7970e34` 的三個 commit（`e9ca81e2`、`9b04a3c8`、`1126991c`）。本輪在同一個 head 上補審查 <https://github.com/ZhiQiYang/geometry-axiom/pull/251#issuecomment-6332818768> 的一項阻擋與三項須改。沒有改 `公理層.md`。沒有關閉 #318、#319。

環境：Windows、純 Python。原生探針需要 C 編譯器與 Linux。ChatGPT 已在 Linux 跑過，本輪未重跑。

## 分支實際範圍

相對 `adbaebf9`：

- #318 缺陷 2：牆線上的點改沿水平切線判斷，水平邊中點的 x 等於別處頂點的 x 時不再把 parity assert 撞掉。
- #318 缺陷 1：柱面落在牆階垂直牆上時照物理排出。凹角也看牆線；柱面料在沿牆料經過的地方分段；柱面有一段前面放不下 27 mm 料時報 `RC_FACE_PART_NO_ROOM`。草稿路線 A（把這種核心限制寫成不可施工）沒有留下。
- #319：C3 的左右承接帶用 `x_band` 跨房間分塊量。
- 核心限制與物理衝突分開。`conflicts` 只放物理上排不出的原因；I19／I22 表示不了的端面在 `core_limits`。`verdict()` 是 buildable／core_limited／unbuildable／inconsistent。沒有物理衝突的排法跑完整 `check()`。core_limited 要求 C8 以外的檢查通過，而且 C8 失敗與宣告依 `(id, end)` 對得上。
- 預期清單：`step` → `step_core` 528 筆、`step_mirror` → `step_mirror_core` 1056 筆，房間與排法保留；原因碼收成 `CORE_LIMIT_BOUNDARY_END_FREE`。沒有刪案例。
- 已知限制仍在：C11 的 2 mm 縫、沿牆料或併料端面頂柱面料時的 I19 優先級、短於 27 mm 的併料（C10）、牆階在牆中段尚未掃描的房型、淺壁柱 #308。

#318 的施工選擇沒有在這條分支裁定。`framing_oracle.py` 仍是 `if not theirs < mine`（約 1975–1987 行）。審查點名的牆階 y=3662、柱 x=1000–1400／y=3606–3806、左上起鋪板長沿 X：原縫位仍報 `C8_I19_PRIORITY`（mine=3, theirs=3），候選仍有 `C11_MAIN_NOT_BUTTED`，最後仍是 `P182_NO_FEASIBLE_CANDIDATE`。兩個版本的 `公理層.md` blob 相同，C8 檢查區段沒有改寫。本輪只確認條文仍被執行，不宣稱 #318 全案已解決。

## 阻擋 1：159 處原始碼突變收據

綁定成立，沒有重跑那 159 處（上一輪那次約 8627 秒）。

`D:\geometry-axiom-work\framing-oracle-gaps\round22\final\tree-1126991c\geometry-core\framing-template\oracle\` 的九個 oracle 檔，與 `git cat-file blob 1126991c:<path>` 逐位元組相同。命令檔 `srcmut-cmd.txt` 寫的 SHA 是 `1126991c9dbd3de92d8cce6eab2419f8f7970e34`。`9b04a3c8` 那份部分副本雜湊不同，而且沒有 `render.py`，沒有拿來當收據。

命令（摘自 `srcmut-cmd.txt`）：

```
sha 1126991c9dbd3de92d8cce6eab2419f8f7970e34
cmd: python -B run10.py <tree-1126991c 的 oracle 目錄> <final\srcmut>
SHARD 0/1, BelowNormal, sequential
start 2026-10-20T09:55:22Z
end 2026-10-20T12:19:10Z
```

每一處要求舊字串出現剛好一次，然後跑 `python -B selftest.py --mutants-only`。日誌沒有「原始碼對不上」。

原始統計：159 處、標題互不重複。exit 1 共 156 處，exit 0 共 3 處。逐處結束碼在 `tally.txt`。exit 1 且轉紅行數是 0 的只有 `X3_no_wall_on_seam_probe`（selftest 當掉），不是存活。

三處 exit 0 的判讀寫在同目錄 `README.md`，這裡只記結論：

- `T2_check_no_noncandidate`：`if dc not in cset` 改成 `if False`。等價。證明沿用 oracle README 第 20 輪：拿掉這條之後，縫位不在候選集合仍會由後面的 C7 報錯。
- `G2_reflex_wall_line_wrong_side`：牆線探測的 0.5 mm 符號對調。本輪用 1126991c 的原始碼只翻這一處，COLSTEP(3000)、COLSTEP(2900)、FZ9、STEP20、FZ145 各 8 個排法，判定、衝突碼、核心限制 `(code, id, end)` 與角材矩形 40 組都相同。G1 拿掉整段牆線凹角時，同一批 COLSTEP(3000) 與 FZ9 在原始日誌裡是轉紅的。幾何上，這條要補的凹角在牆端兩側都還在室內，正負 0.5 mm 都不改變 `ends`。沒有對掃描裡的每一間房證明「沒有任何一間只在一側為室內」。
- `C4_sweep_inconsistent_ignored`：`sweep_family` 裡把 inconsistent 放進問題清單的分支改成 `elif False`。這不是語意等價。`--mutants-only` 走到的 `sweep_family` 沒有產生 inconsistent，所以這條是死路，exit 0。本輪沒有另加對照把 C4 殺掉，原始日誌維持 exit 0。

收進 repo 的檔：`run10.py.txt`、`make_run10.py.txt`（產生器，不是那次執行本身）、`source-mutants.0of1.txt`（LF 日誌，SHA-256 `6ddc819e4c446b44aa41783d43e3d0db1f959c0e38fdfb5290970c90449b8681`，289871 bytes）、`srcmut-cmd.txt`、`expected-spotcheck.txt`、`tally.txt`、本檔。標準輸出是同一份日誌的 CRLF 版，最後多一行 `exit 0 seconds 8627`，沒有再存一份。`queue_0of1.md` 與 `1126991c:決策佇列.md` 的 SHA-256 都是 `c3387507597afafbdf1962b5374d5cfd8187165e6638b7b33c92bb3f794d9f72`，不另存。

## 須改 2：W/2 掃描要斷言不可施工筆數是 0

`_w2_accepts(bad, unb)` 的成功條件是「沒有檢查問題，而且不可施工筆數是 0」。216 個排法的本體掃描與審查指定的對照共用這一個函式。

對照房是 `LROOM(3000, 2600, 1500, 913)`，外框等於

```text
[[0, 0], [3000, 0], [3000, 1687], [1500, 1687], [1500, 2600], [0, 2600]]
```

八種排法各多一個 `REVIEW_W2_REGRESSION` conflict。對照要求：外框對得上、`_w2_accepts` 失敗、不可施工 8、檢查問題 0。失敗列帶 `W2_UNB_NOT_ASSERTED`。另外三間具名 L 形房（3600×3000 缺 1800、4000×3000 缺 2000、5000×4000 缺 2500）沒有改。

## 須改 3：golden 的 core_limits 對回料件

記錄改成 `[碼, 建構端 id, 端面, 矩形]`。id 仍是 `build()` 給的編號，不是排序後 `timbers` 的索引；矩形才對得回那支料。空的 `core_limits` 維持 `[]`。

非空對照放在頂層 `core_limit_witness`，不放進 `rooms`。`gen_scenes.layout_kept` 會跳過有核心限制的排法；STEP20 另有四種板長沿 X 完全可施工，放進 `rooms` 會讓探針多送場景。見證是牆階 20 mm、左上起鋪板長沿 Y：

```text
["CORE_LIMIT_BOUNDARY_END_FREE", 1, 2600, [2600, 3653, 4100, 3680]]
```

排序後的索引 2 才是這支矩形；索引 1（也就是這個 id 的數字）是另一支 `[0, 3673, 2600, 3700]`。selftest 若看到 id 位置的矩形等於限制矩形，會報 `GOLDEN_CORE_LIMIT_ID_IS_INDEX`。64 個既有房間的 `rooms` 內容維持空的 `core_limits`。`test_gen_scenes.py` 60 個測試通過，場景數仍是 64。

這是新的輸出契約。本輪沒有把「現有 consumer 已經錯綁料件」寫成既成事實。`core_limit_problems` 仍只核 `(id, end)`。審查把宣告的 `check` 改成 `C8_MAIN_ON_EXTENSION` 仍 exit 0 的實驗，本輪沒有重做，也不把收據說成「每個原因欄位都已獨立核實」。`CORE_LIMIT_MAIN_ON_EXTENSION` 不要求與單一 C8 碼機械一對一。

## 須改 4：README

- 淺壁柱那一族總數 2×41×4=328。208 個（凸出 28–53 mm）由 `SPAN_PARTLY_RC` 變成沒有物理衝突；56 個（20–26 mm）仍是 `SPAN_PARTLY_BLOCKED`；其餘 64 個（27 mm 與 54–60 mm）前後都沒有物理衝突。舊補記把餘數寫成總數。
- 方向誤植與計數分開寫。審查實測這一族是板長沿 X。方向誤植在 `adbaebf9` 的 README 就有。
- 528 個排法與 668 筆 `C8_I19_BOUNDARY_END` 分開。一個排法可以有兩個受影響端面（壁龕兩個端面；雙牆階例 `DS:3694,3669` 左上起鋪板長沿 Y）。完整檢查後只剩已宣告的 C8 核心限制。668 與「前後都可施工的 64」都來自該審查對 base／head 的比較，本輪沒有重掃、也沒有重跑那 528 筆清單。

## 本輪指令與結束碼

工作目錄 `D:\geometry-axiom-work\grok`。Python 見下方版本列。沒有用 WSL，沒有編譯 `current_geometry.c`，沒有跑 `core-probe/run_probe.sh`。

| 指令 | 結束碼 | 程式印出的結果 |
|---|---|---|
| `python -B geometry-core/framing-template/oracle/selftest.py --mutants-only` | 0 | 三項新檢查為綠；`(--mutants-only:跳過掃描)`。工具記錄 63.91 秒。自證還原後的檔案與這次相同，隨後的 `--ci` 又把同一段跑成綠燈 |
| `python -B -u geometry-core/framing-template/oracle/selftest.py --ci` | 0 | `掃描 8137 次建構(CI 抽樣),235 秒;不可施工或檢查失敗 0 個`。CI 抽樣的 `step_core` 132/132、`step_mirror_core` 264/264。殼層全程 302 秒。W/2 對照 `掃描仍通過=False` |
| `python -B -u geometry-core/framing-template/oracle/selftest.py --quick` | 0 | `掃描 39850 次建構(快速),922 秒;不可施工或檢查失敗 0 個`。`step_core` 528/528、`step_mirror_core` 1056/1056、`reflex` 0/0、`step_mirror` 0/0。殼層全程 988 秒 |
| `python -B -u -m unittest geometry-core.framing-template.core-probe.test_gen_scenes` | 0 | `Ran 60 tests in 57.686s`、`OK` |

Python 3.14.4（MSC v.1944 64 bit）。

## 突變自證

每一項都是暫時拿掉修正、跑 `python -B geometry-core/framing-template/oracle/selftest.py --mutants-only`，看失敗列的病因，再把位元組還原。還原後三個檔的 SHA-256 與改動前相同。

| 拿掉什麼 | 結束碼 | 秒 | 失敗列指出的病因 |
|---|---:|---:|---|
| `_w2_accepts` 改成只看 `not bad`，不再要求 `unb == 0` | 1 | 74.1 | `W2_UNB_NOT_ASSERTED`，且 `掃描仍通過=True`。216 筆本體掃描仍是綠燈（不可施工 0） |
| `core_limit_rows` 不再附矩形，退回三元組 | 1 | 77.9 | `GOLDEN_CORE_LIMIT_UNBOUND`（見證與檔案不一致，並帶 `GOLDEN_CORE_LIMIT_WITNESS`） |
| README 的「其餘 64 個排法」改回「其餘 328」 | 1 | 76.5 | `README_REMAINDER_328`、`README_REMAINDER_64_MISSING` |

## 沒有驗到的項目

- ChatGPT 已在 Linux 跑過，本輪未重跑。該次（審查自述，不是本輪的結束碼）是：核心 `cc` exit 0；`run_probe.sh` exit 0；64 場景、2936 支角材：接受 2624、容量拒絕 312、規則拒絕 0、執行錯誤 0、幾何不符 0。預設 8 MiB 堆疊曾 SIGSEGV，同一支執行檔提高到 64 MiB 後完成。容量拒絕的 312 支沒有進入放置規則。README 裡 `94eae4a3` 的舊探針數字仍是歷史紀錄。
- 159 處原始碼突變沒有在本輪重跑。收據綁的是 `1126991c` 的 oracle 檔，不是本 commit 改過的 `selftest.py`、`make_golden.py`、`README.md`、`oracle-golden.json`。
- 淺壁柱 328 個排法、以及 528 個排法上的 668 筆端面，本輪沒有重掃。
- G2 的符號對調沒有對每一間房證明等價。
- C4 那條 inconsistent 分支仍是死路，本輪沒有殺它。
- 宣告裡的 `check` 欄位沒有另做「改碼仍 exit 0」的實驗。
- C5 對短於 `min_piece` 的橋接缺口多了一個例外。審查沒有把它做成與 `公理層.md` 的具體矛盾；本輪也不把它報成條文矛盾。它已經寫在推論表。

## 最不確定的地方

`C4_sweep_inconsistent_ignored`。原始日誌是 exit 0、轉紅 0，原因是這次 `--mutants-only` 沒有走到 inconsistent，不是因為拿掉該分支後行為仍等價。其次是 G2：五間房、40 個排法的抽查與「牆端兩側都在室內」的幾何說明，蓋不住「有一間房只有一側在室內」的可能。
