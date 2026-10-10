# 2026-10-10 收攏鏈的 WSL CI 等價驗證收據

本目錄收存 PR #180（`fix/closeout-wsl-red-20261010`，合併 head `6615db6`，merge
commit `c254e1f`）在合併前用 WSL 跑的 GitHub Actions 等價驗證，以及相關探針與
判讀。全部是文件/證據，不含產品碼。

## 為什麼用 WSL 代替 CI

GitHub Actions 因帳號計費被阻擋，無法當合併裁判。改用本機 WSL2
（Ubuntu 24.04, Chrome 153）執行與 `.github/workflows/integration-tests.yml`
等價的流程：從受測 SHA 自己的 workflow 讀出 job、env、matrix 與 run script，
在 clean detached clone 上逐字執行；`actions/checkout` 以本地 clone 取代、
artifact upload 略過（無處上傳）。

## Runner 與裁判規則

`runner/` 是當時的執行器（`wsl_ci.sh` 入口，`ci_run.py`/`ci_job.py` 主體，
`make_teeth.py` 牙齒驗證產生器，`baseline_sources.txt` 基線清單）。
三條裁判規則：

1. **Timeout**：hard watchdog = yml 的 `timeout-minutes` × 3.0。超過 CI 上限只標記
   不判紅；撞到 watchdog（exit 124）才是紅。
2. **Flaky**（僅 native）：失敗 suite 在同一 clone 單獨重跑（至多 2 次），只有
   「重跑通過且每個失敗 test id 在 main 基線收據裡也失敗」才算 flaky-rerun-pass；
   瀏覽器 job 任何斷言失敗即紅，不可免除。
3. **Exclusive**：開跑前有界等待其他 session 的編譯/測試行程結束，跑程中每 15 秒
   取樣，兩者都記錄。

**牙齒驗證**：`receipts/345fabb5-teeth/` 證明裁判不是橡皮圖章——在 main 上加一個
只存在 WSL 的突變 commit（M1 恆錯斷言、M2 首次必敗非基線、M3 基線已知 flake
首次注入），native 如預期紅並點名 M1/M2、M3 被正確免除。

## 合併 head `6615db6`：7/7 綠（無 flaky-rerun-pass）

收據 `receipts/6615db61/`（官方 verdict 見其 `receipt.json`）。

| job | exit | 斷言 |
|---|---|---|
| native | 0 | 2610 過 / 0 敗 / 1 允許 skip（合計 2611，83 suite，與 `tests/run_all.expected.json` 完全相符） |
| assembly | 0 | 150 / 0 |
| documents | 0 | 47 / 0 |
| grid | 0 | 346 / 0，completed:true |
| canvas | 0 | 2207 / 0，completed:true，golden matched（84 段），P73 ✓ |
| space | 0 | 228 / 0 |
| timber | 0 | 79 / 0 |

其他收據：`5cc1ffa1`（main 基線）、`a7bff8f4-pr169`、`72a3cbf4-pr179`
（PR #179 head，grid/canvas 紅的修前基線）、`5bf5a6d5-p73-timing` 與
`c7ed80aa-p73-revert`（P73 驗證，見下）。

## P73 判讀（全文：`p73-verdict.md`）

`6615db6` 把 canvas P73 的固定 `sleep(180)` 改成等 `[data-edit-guide]` 列實際渲染
（上限 30 秒）。因為改的是測試，合併前做了三項驗證：

- 加時間戳重跑：`!oc.busy` 成立到 DOM 列出現實測 **437ms**——舊 180ms 真的不夠，
  新等待是確定性完成條件，不是掩蓋。該次 canvas 全綠（6615db6 第二次確認）。
- 還原 `sleep(180)` 重跑：同一斷言必紅（`receipts/c7ed80aa-p73-revert/`），
  與修前基線 `798d8387` 逐項相同。
- FATAL_UI 裡的 `connection.error`「無法確認載入結果」是 **P61-10/P61-11 刻意
  注入斷線測試留下的殘留欄位**（復原後沒有程式清它），通過的 run 也存在，
  與 P73 成敗無因果。

兩次 canvas 的完整 `job.log` 附在 `receipts/6615db61/canvas-job.log` 與
`receipts/c7ed80aa-p73-revert/canvas-job.log`。

## ⑤ 探針（Issue #123 空間卡第二下點擊被 #btnZoom 接走）

`q5-probe/`：忠實移植原始重現（空間卡 `.ocard[data-kind="space"][data-id="1"]
.ocard-frame` 真實雙擊，只用 `Input.dispatchMouseEvent`），slots/beam ×
1400/390 四格。結果：

| SHA | slots-1400 | slots-390 | beam-1400 | beam-390 |
|---|---|---|---|---|
| main `5cc1ffa1` | ✓ | **✗ 落在 #btnZoom** | ✓ | ✓ |
| 鏈頂 `72a3cbf4` | ✓ | ✓ | ✓ | ✓ |
| 合併 head `6615db6` | ✓ | ✓ | ✓ | ✓ |

main 的失敗訊息指名 `#btnZoom`，且 4 取 1 敗圖樣與原始證據一致——探針有牙齒。

## 未驗項

- 實機（非 WSL2 虛擬機）上的瀏覽器行為。
- Windows 原生環境的全量測試（native 基線只在 WSL/Linux 跑過）。
- Resume 的當機、重載、跨 session 情境（本次只驗 bounded Resume，收據見
  `tests/evidence/cloud-takeover-20261009/safe-resume/`）。
- Issue #123 其餘 43 項已知競態（本次只驗 ⑤ 空間卡雙擊）。

## 路徑說明

各收據 README 與 log 裡出現的絕對路徑
（`/mnt/c/Users/Yang/.../scratchpad/`、`/root/ga-ci/`、`/tmp/ga-ci/` 等）
是當時本機 WSL 執行環境的實際路徑，為收據的一部分，不應視為可重現的固定位置。

另外：`q5-probe/*/build.log.txt` 與 `server.log.txt` 原檔名是 `build.log` /
`server.log`，因 root `.gitignore` 全域忽略這兩個檔名，收進來時加了 `.txt`
後綴，內容未改動。
