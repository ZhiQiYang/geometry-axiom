# R12／Q38j 真瀏覽器撤回原件（head abb3da24，2026-11-17 雲端）

PR #430 審查 6942749535「須改 1」要求的原工具完整輸出。這是
[6941334315](https://github.com/ZhiQiYang/geometry-axiom/pull/430#issuecomment-6941334315)
所摘要那一次 `tests/r12_browser_evidence.py --withdrawals` 的原檔，未重跑、未改寫。

- 來源 commit：`abb3da24c870a405f3b0c7a2fea8e4d902a18d4f`（tree `c09b9963a1c574be6a0a025f7a7025eba38d212e`）
- 指令：`LANG=C.UTF-8 LC_ALL=C.UTF-8 GEOMETRY_CHROME=/usr/bin/google-chrome python3 tests/r12_browser_evidence.py --out <repo 外新目錄> --withdrawals`
  （`ulimit -s 16384`；Linux 雲端容器；`/usr/bin/google-chrome` 是 Playwright Chromium 包裝，以 root 執行時自帶 `--no-sandbox`，工具本身 `sandboxFlagsAdded: []`）
- 工具原時限 `timeoutSeconds: 2100` 未改。`summary.json` 為 `status: passed`、`officialMutationLedgerWritten: false`、`goldenWritten: false`。

## 檔案

`raw/` 是工具 `--out` 目錄的原樣副本，除下列兩類外逐檔保留（`raw.sha256` 列出每檔 SHA-256）：

1. **`source-files.json` 未放入**：8,868,998 bytes，是凍結來源全部 40,951 個 Git 檔的 bytes／SHA-256。已核它與 `git ls-tree -r abb3da24` 的檔案集合完全相同、逐檔內容全符；`regen_source_files.py abb3da24c870a405f3b0c7a2fea8e4d902a18d4f` 從 Git 物件重產的位元組 SHA-256 為 `68611dc136ef58fd5ce2916042512ddd44f4c56b63e8fcb474670462a3804c76`，等於 `summary.json` 的 `sourceManifestSha256`。
2. **截圖 `final-state.png` 與瀏覽器下載的 `profile-space-downloads/*.gcanvas` 未放入**（審查清單未要求；後者是測試流程中由一般存檔入口產生的專案檔）。

`sparse-archives.json` 為 `{}`（count 0）：此次凍結的是完整簽出，沒有略過任何歷史收據。

## 逐次執行核對

全部 13 次：`timedOut: false`、`runtimeBefore.fresh: true`、`runtimeUnchanged: true`、`error` 無。
mutant 的三個失敗名中，`complete browser flow` 與 `space group completeness` 是工具 `GENERIC_FAILURES`（流程因指定斷言中止後的必然結果），具名失敗恰為一個，且等於該撤回的指定斷言。

| run | exit | 秒 | profile-space 過／敗／應 | 總 過／敗 | 具名失敗 |
|---|---:|---:|---|---|---|
| baseline | 0 | 189.7 | 60/0/60 | 64/0 | — |
| R12-B01-visible-space-entry | 1 | 21.9 | 8/1/60 | 10/3 | `R12_SPACE_ENTRY` |
| R12-B01 restored | 0 | 167.7 | 60/0/60 | 64/0 | — |
| R12-B02-source-renders-candidates | 1 | 22.2 | 9/1/60 | 11/3 | `R12_ALL_WORLD_CANDIDATES` |
| R12-B02 restored | 0 | 187.8 | 60/0/60 | 64/0 | — |
| R12-B03-no-default-selection | 1 | 22.6 | 10/1/60 | 12/3 | `R12_EXPLICIT_SELECTION` |
| R12-B03 restored | 0 | 169.5 | 60/0/60 | 64/0 | — |
| R12-B04-shared-material-switch | 1 | 31.2 | 22/1/60 | 24/3 | `R12_SHARED_MATERIAL_SWITCH` |
| R12-B04 restored | 0 | 169.0 | 60/0/60 | 64/0 | — |
| R12-B05-overlap-notice | 1 | 30.6 | 21/1/60 | 23/3 | `R12_MATERIAL_NOTICE` |
| R12-B05 restored | 0 | 168.5 | 60/0/60 | 64/0 | — |
| R12-B06-update-candidate-entry | 1 | 48.5 | 33/1/60 | 35/3 | `R12_UPDATE_EXPLICIT_CANDIDATES` |
| R12-B06 restored | 0 | 165.3 | 60/0/60 | 64/0 | — |

## 與現行 head 的關係

`abb3da24` → `46a6aaa5` 只改四份 Mutation evidence 產生物（`tests/mutants_results.json`、`geometry-core/domain-decoupling/` 下 `PRODUCT-ARCHITECTURE.md`、`product-architecture-receipt.json`、`product-architecture-scan.json`）；這四檔不被瀏覽器、服務或原生建置讀取。本目錄與 `需求帳.md`、`.gitignore` 允許清單一行是之後才加入的文件／證據，亦不在其執行路徑內。
