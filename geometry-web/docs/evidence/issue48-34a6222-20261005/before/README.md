# 原缺口失敗收據（不算最終 pass）

- `store-gap.log.gz`：正式 store 接線前，在原 main source 上測證據-only 保存，2 fail / 1 pass；錯誤為未知附件種類/版本。這個初期重現使用當时測試草稿，不宣稱它是最終 clean head 測試。
- `native-stale.json`、`native-stale.png`、`native-stale.log.gz`：`04abd6e` 實作的同 host 由正常 `apiRequest` engineering-confirm 將值改成 458 後，仍顯示 915/2、confirmed-content、checked true、沒有 rebind。測試沒有用會 rerender 的 EngineeringAdapter 代替這個事件，原文字為 synthetic。
- `pdf-resource-gap.log.gz`：針對 `04abd6e` 原 reference-workspace source 的三個選定 regression 全失敗，created 1 / destroyed 0；不把未選定案例算 pass。最終正式 Worker 與 VM gate 已驗清理成功。
- `04abd6e-node-failure.log.gz`：最初完整 Node 結果有 32 个舊 VM fixture 的 structuredClone 缺注入失敗；最終修正 harness 後497/497。失敗原日誌保留，不把舊 head 的任何 full 結果當新 head 成功。

最終驗收只由上層 `receipts/formal.json`、`receipts/summary.json` 與 `logs/` 證明。被中斷的舊 CDP run 不在最終成功統計中；此目錄不是未解的產品失敗清單。
