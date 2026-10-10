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
