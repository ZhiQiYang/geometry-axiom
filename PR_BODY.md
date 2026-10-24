把角材容量從 64 擴至 512，將 W 單一常數連到 H admission、document arrays、contact、cut-list、span scratch，並在 validation callback 前拒絕超容量。七個具名編譯契約防止 H／W 容量不同。其他資源容量與公理不改。

本 PR 是 #300 的容量草稿，疊在 #347，已一般 merge #346 的正式證據。尚未完成正式執行，不關閉 #300。

## 唯一 current-state

| 欄位／gate | 目前 SHA 或退出碼 | 界線 |
|---|---|---|
| current source SHA | `0f695866c0ba12d2c70dfd7d40628d0fda0f905f` | parent 為舊 evidence E391；這次只改 H suite、原 generator test helper、expected H count |
| product code SHA | `400a6d0ca50f3aca104fb569c77c8ef753c93355` | 七個產品檔在 current source 未再改；不冒作新的執行 SHA |
| evidence head | `41481f280495e14f5a6905d29784cea3a218df10` | 新 source 出版原流、v5 草稿與獨立靜審；沒有 runtime PASS |
| base／一般 merge | #347 舊 E `6d9d46e8d16af75351924c6d47a078d3eb647cc0`；M `696f7f07846c6224775dab5736bd1dc45541a4bf` | M 第二 parent 是 #346 E `eaf15e239324a6464a04740647afccce3a3c17c7`；未聲稱含 #347 最後 E2e8 |
| 本次套用／一般 commit／push | **0** | 精確三葉；21 個原子命令（20 Git＋1 df）全0、remote精確核對、工作樹乾淨 |
| 本次獨立靜審 | **72/0、21/0、111/0** | 候選、publisher、實際公開 source；不是 compiler 或產品測試 |
| W／H suites | **UNRUN** | AST 7／7；原 H 五方法保留，新增兩個 placed/replay 方法；局部總 AST75 非 runtime discovery |
| 三個測試修正撤回／恢復 | **UNRUN** | count、population、unplaced replay 分別單獨撤回；不可讓早紅遮蔽另一刀 |
| W runtime 控制／H safe guard／七 ABI 控制 | **UNRUN** | 未宣稱 killed；ABI 只有具名 compiler拒絕才算該控制 |
| 原 contact／report／panel | **UNRUN at current source** | 原64 witnesses、panel13、report11保留；舊 SHA 的結果不挪用 |
| 真512放置／載入／重放／513歷史 | **UNRUN** | 測試已加入；沒有執行 generator、bridge 或 C |
| 完整 native／六 browser／專項／效能／stack | **UNRUN** | N128/256/512性能與stack只完成靜態計畫，不新定門檻 |
| 帳本／架構三裁判及四檔 | **UNRUN** | root 在最後組合來源統一處理，沒有自行重產帳本 |
| skip | 沒有新增允許項 | 尚未正式跑，不能宣稱零 skip |
| 狀態 | **NOT READY** | 所有 runtime gate 待真執行與反證 |

本次修正兩個新測試的契約錯誤：`objects` 只列 placed，原 helper 卻用它計算未放置宣告；`loadfile` 依 I9 拒絕未放置場景，原測試卻期待成功。改用 canonical dump 核對完整 ID 序列與唯一性，另驗 objects 為空／沒有 place。滿容量宣告與未放置 canonical replay 改走真互動逐條 line；原兩個 unplaced loadfile 保留為 I9 拒絕與完整回滾負例。產品 I9 沒有修改。原靜審未查出這兩點，保留歷史報告，不把先前靜審當成執行通過。

另外新增原 N64 與 N512 的真 placed 成功載入測試：沿原 P-189 generator，從 DSL 獨立推導矩形，再驗真 bridge 的角色、ID、長度、方向、右手座標框架與四角；兩個新進程的同一 replay protocol 完整 stdout 原 bytes 相等。512 逐條重放與 loadfile 比較 canonical text/hash 和幾何，正常 valid513／缺ID拒絕保持完整 dump（含 revision/hash）；delete／undo／拒絕／redo／undo 保葉節點與歷史。這些都是**尚未執行的斷言**，不聲稱 UI、完整施工、RC／凹角或效能已驗。

安全邊界不變：撤容量 guard 只送 direct API／缺ID sentinel，不對失去 guard 的固定陣列送 valid513。七個 ABI 控制只接受指定 typedef 診斷後恢復原值真重編；不執行混用容量的物件。新 placed batch 用 binary mode 保存原 stdout，未放置 BridgeSession 的原管線在正式封裝時須另保全，不能把 subprocess.run observer 當成已捕獲所有 Popen 流。

舊 E `391f44da1c3e37e50c7a25a8a855b93c2865062c` 的 578-member／751,021-byte 原件包及先前 15-leaf source 檢查只屬 S400 歷史；原件不改寫。本次採用 v5，v1～v4 草稿及 peer matcher 初錯誤保留；R18 只精確移除被刪 leaf 的具名注解，未清掉其他注解或放寬 golden。

未改公理、決策佇列或 K。既有64 witnesses保留；原容量斷言依授權同步512／513／3328，其餘斷言與時限不放寬。最不確定的是實際512放置成本、stack與完整跨層行為，必須由 current source 的正式收據判定。
