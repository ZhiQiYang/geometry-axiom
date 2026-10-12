# #189 受控診斷的聲明界線

本文件更正 [dot 6116105245](https://github.com/ZhiQiYang/geometry-axiom/pull/189#issuecomment-6116105245) 指出的範圍。產品／裁判來源仍為 `b40620cd433ae36c6a3905c4293313dfd6e7f745`；本次只有文件及唯讀核對，沒有重跑瀏覽器、native、mutant 或七 job。

[原 32 payload＋manifest 的 ZIP](https://github.com/ZhiQiYang/geometry-axiom/pull/189#issuecomment-6115997361) 保留原 bytes：222289 bytes，SHA-256 `3b8be9cc3961f58c7324d9076944f08a63b5c88cd971864014a54b1677a44993`。原 README 的「scrollTop 復位，World dump／history 均不變」限縮如下；本文件與更正後的作者回覆是目前聲明，不改寫 ZIP 中的歷史原文。

- `nodeReplaced:true`、換節點後的 `newRect` 及 `hit:false`，只證明正式 `openSystem` 重建了節點，而新控制項位於畫面外。沒有直接量測前後 `scrollTop`，撤回「scrollTop 復位」的量測聲明。
- `dumpUnchanged:true` 只記錄兩次回應的 `.text` 相等。沒有先核兩次請求 `ok`、字串型別或完整回應，不能擴稱完整 World 零寫入。
- `historyUnchanged:true` 只記錄 `ReferenceWorkspace.history.undo.length` 相等；沒有比較 undo entry、redo 或完整 history 值，不能擴稱完整 history 不變。
- 原 Node driver 記錄這些布林，未對這個完整狀態下斷言。原件沒有 Python receipt wrapper 全文、服務啟停原件或 foreign census，不能據此建立完整隔離或零寫入強結論。先前對自有程序退出的工作紀錄，也不等於這些封包原件已交付。

仍可採的範圍是原 P88 三個斷言的局部 Chrome 診斷：natural exit0；受控 old1→candidate0→revert1→restore0。紅輪在前兩個原斷言後因指定 `#igNewBinding` 不可點而失敗，綠輪完成第三個；候選 helper 來自 #197 `a389de37e2d4683b27aee673c51956a7a40c429b`，未放寬 hit／disabled／尺寸／12×70ms。這些診斷退出碼、原 stdout／stderr、driver 及來源原文保留；不撤銷已核診斷，也不新增測試或 killed 計數。

`audit.py --zip <還原的原ZIP>` 只讀原件，核全部 32 payload hash、五份既有退出碼、四份受控觀察與 driver 的實際比較欄位。本次 audit exit0 只證明這些原件及聲明界線核符，不能把布林觀察升級為新的產品斷言。audit 的 stdout／stderr 與直接 subprocess.run receipt 附於本目錄。

原 canvas 1401/0、completed=false、exit1，space165/2、exit1，歷史自然首紅、最終同 SHA 完整驗收及無 main 豁免界線均保留。沒有將 space:678 認成已證原680同因；維持 draft，由既定 landing owner 承接。
