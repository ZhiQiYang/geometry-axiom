# 獨立唯讀審查判定

本審查讀取 AGENTS、PRODUCT-VISION 與 SSOT I8／I8a，再比對遠端 #173／#174、既有證據及整合候選。未修改產品檔案，未代替既有本機 owner 接管 app.js。願景草案不作新實作授權；拒絕維持 World 原狀沿用既定契約。

**已由真 browser 補足來源推導**：`#174@4e6ab4421e0e634ff4fd06356dadb7d8eaf4feb3` 的 app.js `drawEditHandles` 在 await uvMap 後確認 token 過期，卻仍呼叫全域 `previewClear()`。在整合候選 bdd1bf78，實際扣 A 的原生 proj 回覆、切換並讓 B 畫完再釋放 A，於桌面及390px都刪除了B手把。各自的完整 World 維持不變。這是介面歸屬缺陷，不是 core 幾何拒絕。

**#173 的兩個 reject handler 同根因仍在**：`#173@d44ad7fea531a94f67401d5b403565cd891770ae` 的 face／main 邊長 listener 只依 `inp.isConnected` 重設 defaultValue。原節點還在但使用者已打新值時會清掉新值；原節點被換掉時則沒清掉原提交值，下一次 capture／restore 又保留已拒絕值。本包真 native 拒絕在兩尺寸、兩 pane 都再現這兩條。

這兩 pane 都是 `setView3(false)` 後的物件畫布／面內工作區。#173 的三視圖直接編輯及 pending edge 回覆跨模式切換仍未驗；只有 #174 handle probe 點了 #btnObj 進三視圖。scene 裡有 placement 不能證明曾走該 UI。success-sibling 的首筆 native `ok:true` 證明成功套用路徑到達，但其完整 draft 保全條件失敗，不可寫成成功套用驗收完成。

此外，真 browser 的 replacement-new-value／success-sibling 控制呈現額外 trusted change 及 native 修改，沒有維持「值尚未送出、模型未改」的條件。這是已記錄的 browser 觀察；具體事件根因仍須唯一產品 owner 審查，不由假 DOM 控制結果推定。沒有把 source-only probe 通過冒充真 browser 通過。

**仍只到來源層的相關審查**：canvasDown 的 uvMap／bhit、canvasMove 的 uvMap、canvasUp 的 emitBoundary 後續與 uvMapFor cache 寫入，仍須檢查工作世代、工作面及專案歸屬。held bhit 在私有非browser定序探針會於離開edit後建立editDrag；本公開包沒有它的真browser驗證，所以不能稱其已browser失敗。也不能為修 drawEditHandles 一個點而宣稱所有 await 都已成立。

舊 #174 原 before／after 收據的十份 LF 來源 hash 與 Git 相符，證明其原有「boundary晚回覆後切view」及「投影確認期間保住高度欄焦點」局部輪可追溯。那個探針沒有扣 proj，也沒有覆蓋 A→B 手把情境。#173 已提交包的六份檔案 hash 相符，其 Windows app hash 與 Git CRLF 展開相符；但原 probe／原始 stdout 仍缺件，13／1／1不能升格完整验收。歷史 #btnObj 被影響對話框遮住是前置阻塞，不能寫成邊長缺陷。

受測 bdd1bf78 的 app.js／space-workspace.js 在各輪開始結束 bytes 一致；當時 repository 有兩個 untracked integration probes，binding 明列 dirty 狀態，未包裝為 clean。新文件或後續提交即使產品bytes相同，也不是本輪實跑的full SHA。

判定：兩項仍需產品修正與精確候選回歸，尚非可合併，也不能列為只剩外部條件。原失敗輪、失敗代表、前後 dump 和當輪脚本保留；没有為迎合產品輸出調整行為判定。
