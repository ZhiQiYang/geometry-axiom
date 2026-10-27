# 本機 WSL 對 F 的參考結果(不算正式驗收)

- F = `a6f4013364e21bcb7239b5dcc25caac0f6d61f77`(S10 加 2026-10-26 裁決一節)。
- F′ = `a4bd77e8090f5a82f0c8934c30c5335782293922`:F 加上本資料夾 `arch-regen/new4/` 的兩個架構產物檔(`PRODUCT-ARCHITECTURE.md`、`product-architecture-receipt.json`),逐 byte 相同。
- 執行者:本機 Claude(session `f46787ac`),Windows 11 上的 WSL Ubuntu-24.04,2026-10-26 至 10-27(台北)。
- 這台機器比雲端慢約 2.4 倍,native 與 canvas 超出 CI 時限。**F′ 的 7 項與閱讀 A oracle 正式驗收交給雲端 Codex 重跑**(使用者 2026-10-27 選「交給雲端 Codex 跑」)。本資料夾只是對照。

## 結果

| 項目 | 來源 | 退出碼 | 耗時/時限 | 摘要 | 原件 |
|---|---|---|---|---|---|
| 架構四檔重產 | F | 工具 ALL PASS | — | manifest、scan 逐 byte 不變;只改兩檔;unit 205+18 tests、0 skip;掃描 334/6/798/0;input closure `8d47b620…` 不變;SSOT snapshot 等於 F 的 `公理層.md`、`決策佇列.md` | `arch-regen/regen.log` 第 124–145 行、`arch-regen/compare/` |
| 閱讀 A oracle `tests/test_geo318_reading_a_oracle.py -v` | F | 0 | 2.7 s / 300 s | | `oracle/receipts.jsonl` |
| oracle `selftest.py --mutants-only` | F | 0 | 51.2 s / 1200 s | | 同上 |
| oracle `selftest.py --quick` | F | 0 | 855.0 s / 7200 s | | 同上 |
| assembly | F | 0 | 322.7 s / 15 分 | | `wsl-ci/browsers/` |
| documents | F | 0 | 109.3 s / 10 分 | | 同上 |
| grid | F | 0 | 633.1 s / 15 分 | | 同上 |
| space | F | 0 | 362.2 s / 15 分 | | 同上 |
| timber | F | 0 | 243.1 s / 20 分 | | 同上 |
| canvas | F | 1 | 2636.9 s / 35 分(超時) | 2265 過、3 敗:P52-3 H at-line guide 2 A27 的 `+u-n`、`-u+n` 兩條,加上因此觸發的段落下限 `[CDP FLOOR] 段 P52:預期 43,實得 41`;同時段有 `[API TRANSPORT FAILURE]` | `wsl-ci/browsers/canvas/job.log` 第 817–818、852、2864 行 |
| native | F | 1 | 4748.4 s / 35 分(超時) | 5329 中 5326 過、2 敗、1 允許 skip;2 敗都是逾時(`tests/test_engineering_project_store.js:155`、`tests/test_reference_workspace_races.js:4`),job 內單獨重跑 `node:tests-js` 為 0;`mutation:check` 紅:killed 62、crashed 1、survived 0、equivalent 4、invalid 0、stale 53、blocked 0、retired 3 | `wsl-ci/native2/native/` |

## 注意

- `arch-regen/regen.log` 結尾的 `overall=HAS-FAILURES` 來自安裝後額外加跑的 `tests/test_product_architecture.py`:它在 WSL 讀 `/mnt/d` 時卡在 9P(`p9_client_getattr_dotl`)42 分鐘,本機 Claude 核對命令列與 cwd 後結束該行程(exit 143)。同一測試在工具本身的 51 條命令中已跑過:18 tests、0 skip、0 fail(`regen.log` 第 137 行)。
- 省略了 `arch-regen/judges-after-install/tmp/`:那是測試期間複製出的整份產品暫存樹(含一份閱讀器副本),不是證據;放進 repo 會違反「閱讀器只准一份」。
- `SHA256SUMS` 記錄本資料夾每個檔的雜湊。
