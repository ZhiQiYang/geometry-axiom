# PR #202：完整 space 失敗的後續診斷

回應 [dot 6111325158](https://github.com/ZhiQiYang/geometry-axiom/pull/202#issuecomment-6111325158)。
原 [13 pass／2 fail](../review-dc4e929/raw/browser/space/result.json) 與
[服務端六次 BrokenPipe](../review-dc4e929/raw/browser/server.log) 原件保持不變。
本輪不是為補可得性重跑，而是針對原 `projection definition closes` 失敗診斷。

## 結果與界線

1. 先在原 harness 以記憶體插樁記錄 trusted click／dialog close；
   `projection-lifecycle` 原 18 個斷言全過，沒有重現原逾時。
   之後**刻意停止**，aggregate 20 pass／2 fail、exit 1、completed=false；
   兩 fail 是診斷停機及未完成 census，不能當完整 space 通過。
   [事件觀測](run/fp-diagnostic.json)、[原結果](run/result.json)、
   [診斷 log](diagnostic.log)、[插樁 harness](run/instrumented-harness.js)、
   [插樁執行器](diagnose.cjs) 均保留。未改 tracked 原碼。
2. 接著跑**未插入觀測碼的原 runner**，無 scope filter：
   **228 pass／0 fail、exit 0、completed=true**。
   setup 2、projection-lifecycle 18、space-height-library 112、
   projection-placement 36、font-layout 19、space-flow 39、browser-health 2
   均達原 expected 且 completed；exceptions／consoleErrors 均空。
   [完整結果](original/result.json)、[原始 log](original.log)、
   [最終畫面](original/final-state.png) 可讀；另附 [桌面投影](original/projection-definition-desktop.png)
   與 [手機投影](original/projection-definition-mobile.png)，原 suite 的桌機／手機流程均有執行。
3. 本輪服務 log 的 BrokenPipe 為 **0**；[server.log](server.log) 保留。
   不推定舊六次是此次逾時原因，不把單輪成功稱為已找到根因或修復產品。

## 身分／命令

受測 head `4ec01328296f4370438445ad60beb7c7a1de8357`，完整 tree 見
[metadata.json](metadata.json)。服務獨立使用 18844，Chromium CDP 9349；
`Browser plugin not available`，沿原 Chromium harness。
原 CLI argv 與全部相關非機密 env、源碼 hash、main 同 blob 比較均在 metadata。
`app.js`、`space-workspace.js`、`space_model_test.js` 與 main 同 blob；
這不是 main 同測試失敗證據，也不證明 C2 不可能影響執行。

服務經 `start_local.py --port 18844` 驗證並沿用具有內容雜湊／fresh sidecar 的專用
core／bridge／model-base。runtime 前後 fresh、版本／PID／session 相同。
[checkout-during](checkout-during.json) 是開跑後擷取，不能當開跑前收據；
與 [checkout-after](checkout-after.json) 的 head/tree/source 相同、tracked diff/status 空。
[process-snapshot](process-snapshot.json) 只是一次觀測，不是全程 foreign census；
沒有宣稱正式隔離。測後保全 [native dump](final-native-dump.json)，再僅停止本工人
18844 服務與測試 browser，未動使用者服務。

本目錄來源為 repo 合成夾具，不含私人圖紙或使用者回報資料。
[sha256.json](sha256.json) 核對 raw（不自列 manifest／此說明）；
[保存腳本](save-diagnosis.py) 保留採集方法。

## 尚未解除

原逾時這次未重現，**根因仍未證實**。沒有 main 同測試失敗證據，
不能依 P-051 把原紅燈豁免為 flaky，亦不能以此 Linux 局部成果取代正式裁判。
本輪未跑 native／reader 三道、其他六 job、golden 或 WSL；不是七 job 全綠。
正典仍待 #192 既有 owner 在最終整合 head 納入 R7／R15 追溯並同步驗證。
本交付提交只增加證據及說明，不是新提交 head 的驗收；PR 仍 draft。
