# Canvas 外部編排唯讀審查

審查來源為 `run_canvas_job.py`，SHA-256 `a9ea3f2f838dc2738ea1c77cf30b8627e0414e5eae9fd6b391057186d8d45924`。未啟動 build、服務或瀏覽器；核對正式 A `7159530c0e494d3211e6ab1764eb691137211707` 的 harness、golden、runtime 與 trace 封存來源。

核心流程無阻擋：2100 秒總期限早於 build 起算，15 秒收尾保留、trace 封存及二次清理都在同一截止內；完整 SHA、乾淨工作樹及前後來源一致守門；原 `node geometry-web/cdp_test.js`、full scope、既有 2261 golden 與完整 sections 都保留。fresh runtime 須同 root、來源版本及自有 server PID。例外計數依原 `[EXPECTED EXCEPTION]` 分類，沒有把預期 P38 例外誤當未處理產品錯誤。

清理以子程序 session、subreaper、PID/startTime 確認，再經 pidfd 發訊號；不依程序名稱廣殺。清理結果與 archive 例外均寫入最終收據，連接埠以 ECONNREFUSED 核對無 listener。原程序退出碼與外層接受結果分列。

非阻擋事項：assembly 的兩張圖使用 `/tmp/geometry-tests/assembly-*.png` 硬路徑，需另外保留該輪原件及時間/雜湊，不能僅列設定的 screenshots 目錄。PID 重用導致歷史 owned key 無法重新註冊時屬失敗關閉風險；pidfd 不會因此向新 PID 發訊號。

後續實際 A 首輪於 build 後、服務及 browser 前遇到外層字型條件過嚴：`sans-serif:lang=zh-tw` 首選 OpenAI Sans，已安裝 Noto CJK 仍被拒絕。這是外層環境收據問題，不是產品測試紅；執行者保留原輪並修為保存實際首選、另驗直接 Noto CJK 匹配。此審查通過不代表該首輪或最終 L 七項已通過。

修正版 `327e926ae0e88fff4b04e68afdee9fb12e9dd2dff0a839fb340603a9fc20121a` 已再讀字型區塊：新增保存 `defaultSansMatch`，另匹配 `Noto Sans CJK TC:lang=zh-tw`，沒有改系統字型設定或擴大產品測試門檻。A preflight-r2 以新輸出目錄開始，首輪原件保留；此差異不影響上述來源、期限與程序所有權審查結論。
