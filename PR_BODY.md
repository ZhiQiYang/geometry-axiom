# P88：在送出真實滑鼠輸入前確認控制項版面穩定

P88 在 390 px 版面準備切換 `#refGuideMode` 時，原失敗後焦點停在比例欄，未取得指定鍵盤焦點。固定 `13d02c1db7022145a52ee063286a558e595eb212` 的三次獨立完整 canvas 結果為 **1／0／0**，屬間歇失敗。失敗的原斷言是：

```text
UI condition timed out at === P88. 原生來源子線顯示、完整引用、兩面及正式重開 ===: document.activeElement===document.querySelector("#refGuideMode")
```

本補丁只改 `geometry-web/grid_rule_lines_test.js` 的 P88 輸入準備：等待既有 UI settle、重新取得目前節點、捲至可見位置，確認節點與矩形跨兩個畫面更新仍相同，且點擊位置確實命中目標，再送出原真實滑鼠點擊。準備與精確焦點確認共用原 25 秒，原 12 次嘗試上限、所有斷言、golden 與 CI 時限維持不變；新增的是嘗試內的矩形觀測。沒有強制 focus、DOM click 或寫入欄位值。

| Current state | SHA／結果 |
| --- | --- |
| 公開 source commit | `8bce9239c014f070740455556c8ee1176c500af3` |
| 原三輪受驗 SHA | `13d02c1db7022145a52ee063286a558e595eb212` |
| 原三次 full canvas | exit 1／0／0，全部在原 35 分鐘內；兩次通過均 2267／0、golden matched |
| source 語法／diff 檢查 | `node --check geometry-web/grid_rule_lines_test.js` exit 0；`git diff --check` exit 0 |
| source push／remote SHA 核對 | exit 0／0 |
| 真查詢時序診斷 | fixed／withdrawn／restored 原測試 exit 1／1／1；三者皆因工具的位移預條件未成立，總 driver exit 2、proof=false，不算突變自證通過 |
| 最終 F 的正式驗收 | 待主代理合入、刷新架構並固定公開 F；計畫同一 F 連續三次完整 canvas 與一次 grid |
| 允許的 skip | 本補丁不新增 skip；診斷外部 loader 明列只執行原 P88，不能冒充正式 grid／canvas |

真查詢診斷已看到原 `paintQuery`／`renderFaceInspector` 重建節點與 scroll `25 → 0 → 25`，但未重現舊座標命中比例欄。此診斷不是原自然紅的因果證明，三階段失敗原件完整保留；工具在初次量測的預條件檢查即中止，目標位置的候選穩定檢查尚未執行，不能據此判定修正有效或無效。原三輪沒有 pointerdown 目標追蹤；目前不能斷言是哪一個查詢造成歷史失敗。兩個畫面更新的穩定觀察也不能保證未來不再重排，仍須以新 F 的完整驗收評估。

獨立代理已對抗檢查候選差異、原工作流程綁定與最終三輪錄製器，未發現斷言、golden 或時限放寬。本 source commit 尚未完成最終 F 驗收，不能據此宣稱 #288 全綠。
