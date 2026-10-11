# Q38 I44 精確包含 + AC16 故障注入閘：WSL 重驗收據（2026-10-10）

對象：分支 `feat/q38-section-profile-next-20261009` 上的 I44 精確包含修正與 `tests/section_profile_mutation_check.py`（GEO-256「Q38 剩餘切片」）。

## 受驗版本

| 項目 | 值 |
|---|---|
| 受驗提交（rebase 後、加入本收據前） | `f0c4c71291af5cab699f54de8ac852aa35fa378e` |
| 該提交的 tree | `3e13b79b9ec143ed5297bd6a9ee5944d9b18d49f` |
| 基底（origin/main，PR #180 合併） | `c254e1f1d6b0980170f3ffc8b855cd696654bd46` |
| 乾淨 clone | WSL `~/ga-q38c`（開跑前、跑完後 `git status --porcelain` 皆為 0 筆） |

本收據與合約文字是後來才加進同一分支的（amend 成最終提交）。受驗的原始碼與測試就是 `f0c4c71` 的內容；amend 只新增本目錄、修改
`geometry-core/SECTION-PROFILE-NATIVE-CONTRACT.md`，並更新 `tests/section_profile_mutation_check.py` 檔頭 docstring 的一段說明文字（不影響行為）；
沒有動 C 原始碼、Python 製模器、測試或 `tests/mutants_results.json`。最終提交的完整 SHA 見 PR 正文。

clone 是從 `/mnt/d/geometry-axiom`（主 repo）做的，再 checkout 同名分支；`/mnt/d/geometry-axiom-q38` 是 Windows worktree，
它的 `.git` 檔案指向 Windows 路徑，WSL 內的 git 打不開，所以不能直接 clone 它。分支 SHA 已核對相同。

## 環境（`env.txt`）

WSL2 Ubuntu 24.04.5、kernel 6.6.114.1-microsoft-standard-WSL2、gcc 13.3.0、Python 3.12.3、Node v22.20.0（獨立 binary）、
12 核、約 7.5 GB 記憶體、`ulimit -s 16384`。沒有 `python` 指令，PATH 前置了只含 `python -> /usr/bin/python3` 與 `node` 的 shim 目錄。
開跑前用 `ps` 確認沒有 chrome／node／gcc／cc1 行程；這輪 WSL 沒有其他人使用。全程循序，沒有平行的其他工作。

## 指令與結果

| # | 指令 | exit | 結果 |
|---|---|---|---|
| 1 | `python3 tests/binaries.py build` | 0 | bridge／core／engjson／integrity／model-base 皆 fresh（`binaries-build.log`） |
| 2 | `python3 tests/section_profile_mutation_check.py --receipt q38-mutations.json --logs mutation-logs` | 0 | native 與 model 基準線皆 exit 0（零 skip）；**42 例：41 killed、1 equivalent（SPM24）、0 survived** |
| 3 | `python3 tests/section_profile_mutation_check.py --explore --receipt q38-mutations-explore.json --logs mutation-explore-logs` | 0 | 同樣 41 killed、1 equivalent；每例跑整個測試類別，取得實際轉紅的測試清單 |
| 4 | `python3 tests/run_all.py --build` | 0 | 83 個 suite，**2611 測試：2610 pass、0 fail、1 skip**（`py:test_gdi_contract`，Windows GDI，具名允許清單）；`py:test_section_profile_native` 26／26、`py:test_section_profile_modeling` 19／19；各 suite 計數與 `tests/run_all.expected.json` 相符 |
| 5 | `python3 tests/mutate.py --check` | 0 | 48 筆變異、48 筆紀錄：killed 40、crashed 1（M20）、survived 0、equivalent 4、invalid 0、**stale 0**、blocked 0、retired 3 |

第 5 項 stale 為 0，所以 rebase 之後 `tests/mutants_results.json` 沒有過期，沒有重跑任何帳本條目，也沒有改動該檔。
tally 與基底相同。M20 是基準線已通過、同一夾具連三次以存取違規（-11）結束的既有 `crashed`，不是這個分支造成的。

run_all 的總數比先前在開發樹量到的 2592 多，是因為基底從 a7bff8f 前進到 c254e1f，主線新增了測試（`run_all.expected.json` 由主線更新，
本分支沒有動它）。2592 那組數字不再適用。

## 檔案

- `q38-mutations.json`：第 2 項收據（`section-profile-mutations/1`），每例的 binary 雜湊、exit、失敗測試、判定。
- `mutation-logs/SPMxx.log`：第 2 項每例的測試日誌（只跑該例指名的殺手測試）。
- `mutation-enforced.console.log`：第 2 項的主控台輸出。
- `q38-mutations-explore.json`、`mutation-explore.console.log`、`mutation-explore-logs.tgz`（第 3 項；日誌解開約 7 MB，所以壓縮）。
- `ac16-per-case-red-tests.md`：由第 3 項收據產生的逐案例清單——每例實際轉紅的測試、失敗訊息、人工對到的提案 AC，
  以及與提案 AC16 逐條要求的差異。**AC 對應是人工讀測試內容得到的**，測試方法本身不帶 AC 編號。
- `run_all.log`、`mutate-check.log`、`binaries-build.log`、`env.txt`、`exit-codes.txt`。
- `SHA256SUMS.txt`：本目錄全部檔案的雜湊（不含它自己）。雜湊算的是 git 內儲存的 LF 位元組；Windows 以 `core.autocrlf=true` 簽出時文字檔會變 CRLF，雜湊就對不上，驗證請在 Linux 簽出或用 `git show <commit>:<path> | sha256sum`。

## 這份收據證明什麼、不證明什麼

證明：在 `f0c4c71` 上，I44 精確包含修正通過全部非瀏覽器 native／模型測試；AC16 閘門 42 例中 41 例被指名測試以斷言轉紅且訊息含條號或病因，
唯一未被殺死的 SPM24 是真等價（進階框架只可能由 `surface_frame_is_valid` 放行，up = -V 恆合法，D38 的「V 有合法 up」這一項在實作上不會不成立）。
SPM41（把精確面積改回 `poly_contains_rect`）使 `test_concave_not_four_corners_and_winding` 以
`expected rejection 'V_PROFILE_OUTSIDE' but the candidate was accepted` 轉紅（`mutation-logs/SPM41.log`）。

不證明：

- 提案 AC16 的逐條對應。AC23 沒有任何突變把它打紅；AC04、AC05、AC06、AC24 是相似場景（不同座標或輪廓）轉紅；沒有「整個移除面材寬度上限」的獨立案例。
  細節見 `ac16-per-case-red-tests.md` 最後一節。
- 瀏覽器層：`geometry-web/cdp_test.js`、`geometry-web/space_model_test.js`、`tests/test_section_profile_browser.js`、
  `tests/integration/q38_save_roundtrip.py` 等需要 Chrome 的閘門沒有跑（`run_all` 輸出末尾列為「本 aggregate 未驗」）。
- Windows／MSVC 路徑；託管 CI（帳號計費阻擋，Actions job 秒失敗，不是程式失敗）。
- 最終提交本身沒有再整套重跑；它與 `f0c4c71` 的差異只有本目錄與合約文件。
- 核心 `current_geometry.c` 的 D7／I5 路徑（`poly_contains_rect` 的同一弱點）不在範圍內，已另開 GEO-257。

## 來源綁定（2026-10-11 補）

回應 PR #182 整合審查（issuecomment-6100281749）兩項：受測提交查不到、`--only` 接受未知案例 ID。第一項在本節，第二項見下一節。

### 受測提交已推上 GitHub

| 項目 | 值 |
|---|---|
| 分支 | `evidence/q38-tested-f0c4c71-20261010`（只為保存來源；不是要合併的分支） |
| 受測提交 | `f0c4c71291af5cab699f54de8ac852aa35fa378e`（2026-10-11 用 `gh api repos/ZhiQiYang/geometry-axiom/commits/<sha>` 查得到，回同一個 SHA） |
| 該提交的 tree | `3e13b79b9ec143ed5297bd6a9ee5944d9b18d49f`（`gh api repos/ZhiQiYang/geometry-axiom/git/trees/<sha>` 查得到，回同一個 SHA） |

### f0c4c71 與審查綁定的 head（`f752994f96e9d8e62ffd5bd6ab02bc3b39b041a0`）的同一性比較

兩者的父提交都是 `c254e1f`（f752994 是 amend 出來的兄弟提交，不是 f0c4c71 的後代，所以 `git log f0c4c71..f752994` 只會列出 f752994 自己）。
f752994 的 tree 是 `eecf10fe1279b867f6e6ff8976775406524a7324`。

```sh
git diff --stat f0c4c71 f752994 -- . ':(exclude)tests/release-evidence'
git diff        f0c4c71 f752994 -- . ':(exclude)tests/release-evidence'
```

本目錄以外，兩個 tree 各有 10625 個檔，內容不同的只有 2 個：

| 檔 | 差異 | 性質 |
|---|---|---|
| `geometry-core/SECTION-PROFILE-NATIVE-CONTRACT.md` | +76／−6 | 文件：把「待 WSL 重驗」的開發樹數字換成 f0c4c71 的實測結果，加 `--explore` 實測表。沒有任何測試或程式讀這份文件（`git grep` 只有其他文件連到它） |
| `tests/section_profile_mutation_check.py` | +3／−2 | 只有模組 docstring 的說明文字。兩版去掉 docstring 後的 Python AST 完全相同（`ast.dump` 逐字相等），所以沒有任何可執行行為的差異 |

- C 原始碼（`geometry-core/*.inc`、`current_geometry.c`、`geometry-web/*.inc`）、Python 製模器、`tests/test_section_profile_*.py`、`tests/mutants_results.json`、`tests/run_all.py`、`tests/run_all.expected.json`：f0c4c71 與 f752994 的 blob 相同。
- 本目錄（`tests/release-evidence/20261010-q38-i44/`）：f0c4c71 裡一個檔都沒有；f752994 新增 55 個檔（`SHA256SUMS.txt` 列其中 54 個，另一個是它自己）。比較前先把 f752994 裡這 54 個檔逐一算雜湊，與 `SHA256SUMS.txt` 全部相符（0 個不符）。

結論：f0c4c71 到 f752994 只差文件、docstring 與收據，沒有產品碼或測試邏輯差異。上面的「受驗版本」表和「這份收據證明什麼」仍然指 f0c4c71。

### 完整測試是在 f0c4c71 跑的，不是在最終 head

- 第 1–5 項指令（建置、AC16 閘門、`--explore`、`run_all.py --build`、`mutate.py --check`）都是在 `f0c4c71` 的乾淨 clone 上跑的。
- 2026-10-11 的修補（下一節）之後，head 多了 `--only` 守門、新測試檔與 run_all 登記。那些**不在**上述完整測試的範圍內；它們另有下一節的驗證。
- **最終 head 的 7 job 全量由主迴圈另跑，結果會貼在 PR 留言**；本目錄不含那份結果，不能拿本目錄的數字當成最終 head 全套已核。

### WSL 時限條件（照實寫）

- f0c4c71 那五項是在 WSL 直接逐條執行（`env.txt`：20:51:01 → 21:24:36，共 33 分 35 秒），**不是**走 7 job CI 等價 runner，也沒有套任何時限。
- 其中第 4 項 `run_all.py --build` 的 suite 秒數合計是 1128.7 秒（`run_all.log`「合計」列，不含建置；suite 是循序執行）。原 CI 的 `native` job 是 `timeout-minutes: 15`（900 秒），所以這份收據**不能寫成「在原 CI 時限內通過」**：它只證明在沒有時限的 WSL 上通過。runner 的時限是原 CI 的 ×3（45 分鐘），1128.7 秒在其內，但本收據不是 runner 跑的，不據此主張。
- 託管 CI 受帳號計費阻擋（Actions job 秒失敗，不是程式失敗），所以沒有任何託管 CI 的秒數可比。

## `--only` 守門修補（2026-10-11）

### 問題

`tests/section_profile_mutation_check.py --only <不存在的 ID>` 選到零案例，不建基準線、不判任何突變，最後 `all([])` 為真而 exit 0。在 f752994 的檔案上實測：`--only SPM3`（少打一個 0）輸出 `{"summary": {}}`、exit 0（`only-guard-fix-20261011/3-pre-fix-typo.log`）。

### 修法

- `select_cases(only, groups)`：未知 ID 丟 `ValueError`（點名未知 ID，並列出全部合法 ID）；選集為空也丟 `ValueError`（例如 `--only SPM36 --group native`，SPM36 屬於 model 組）。
- `main()` 在 `--list`、`posix_only()`、任何建置之前呼叫它，把 `ValueError` 轉成 `parser.error`：exit 2，不跑任何東西。結束碼 2 沿用該腳本既有的「環境／前置條件不成立」，沒有另立新碼。
- 合法子集的路徑沒有動：基準線照跑，突變照判。

### 驗證

測試：新檔 `tests/test_section_profile_mutation_check.py`（9 個測試，不需要原生二進位）已登記在 `tests/run_all.py` 的 `PY_NEEDS`（`[]`）與 `tests/run_all.expected.json`。**這是新增 suite（`py:test_section_profile_mutation_check` = 9），不是改既有期望**；其餘 83 個 suite 的期望數沒有動，以 f0c4c71 那次完整跑的 83 個 suite／2611 測試為底，預期總數變成 84／2620。

收據在 `only-guard-fix-20261011/`，驗證於修補提交 `f3c87c21a62bc57df761ffe66fea61f6a49a931c`（tree `e7574f7668754c06936ed67646f4830d4a7c6a76`）的 WSL 乾淨 clone，經佇列鎖（標籤 `pr182fix`），`env.txt` 有環境與起訖時間（02:41:22 → 02:47:41，共 6 分 19 秒）：

| # | 指令 | exit | 結果 |
|---|---|---|---|
| 2 | `run_all.py --only section_profile_mutation_check` | 0 | 新 suite 9／9，與 `run_all.expected.json` 登記的數量逐 suite 比對相符（局部跑，不是完整驗收） |
| 3 | f752994 的舊腳本 `--only SPM3` | 0 | 修前：`{"summary": {}}`，未測任何東西卻成功 |
| 4 | 修後 `--only SPM3` | **2** | `unknown --only case id(s): 'SPM3'; valid ids: SPM01, …, SPM42` |
| 5 | 修後 `--only SPM41 --only SPM4l`（合法加錯字） | **2** | 整批拒絕，只點名 `'SPM4l'` |
| 6 | 修後 `--only SPM36 --group native` | **2** | `no case selected: … (SPM36 is in group model)` |
| 7 | 修後 `--only SPM41 --only SPM24 --group native`（合法子集，真的編譯） | 0 | native 基準線 exit 0；SPM41 killed、SPM24 equivalent（與 f0c4c71 的判定相同） |
| 8 | 修後 `--only SPM36`（合法單一 model 案例） | 0 | model 基準線 exit 0；SPM36 killed |
| 9 | 新測試檔直接跑 | 0 | 9／9 |

秒數：建置 157 秒、第 7 項 190 秒、第 8 項 17 秒，其餘各 0–5 秒；這些不是 CI job，沒有對應的原 CI 時限可比。Windows 上直接跑新測試檔也是 9／9（Python 3.14.4）。

突變（把守門拿掉，新測試必須紅；在 WSL `python3` 對工作樹逐一跑，輕量、單一測試檔，沒有排隊鎖；還原後確認 `tests/section_profile_mutation_check.py` 的雜湊與提交內容相同）：

| 拿掉什麼 | 紅燈（測試數／失敗斷言數，後者含子測試） | 失敗訊息 |
|---|---|---|
| 同時拿掉兩道守門（等於修前行為） | 9 個測試裡的 5 個／12 | `0 != 2 : exit 0 means the mistyped selection was taken as a success: no case was selected, so no baseline ran and all([]) reported success`（`guard-mutant-both-removed.out`） |
| 只拿掉未知 ID 守門 | 4 個／9 | 錯字案例退到「空選集」守門仍 exit 2，但訊息變成 `no case selected`，`'unknown --only case id' not found in …` 紅燈；`--list` 加合法與錯字 ID 時 exit 0 紅燈（`guard-mutant-unknown-removed.out`） |
| 只拿掉空選集守門 | 2 個／3 | `--only SPM36 --group native` 與 `--only SPM01 --group model` 變成 exit 0、stdout `{"summary": {}}`（`guard-mutant-empty-removed.out`） |

還原後新測試 9／9 回綠（見第 9 項）。

### 這一節不證明什麼

- 沒有重跑 f0c4c71 的完整測試；沒有跑瀏覽器層閘門。
- 合法子集只實跑了 SPM41、SPM24（native）與 SPM36（model）三例，不是 42 例全量；全量在 f0c4c71 跑過（第 2 項），修補沒有動任何案例定義或判定邏輯。
- 修補提交到最終 head 之間只增加本目錄的收據與本節文字。
