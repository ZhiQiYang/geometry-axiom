# GEO-300 前置：保留順序的擋面去重

本分支目前已一般 merge 新列車 `a6072dde8eac809e93ccd9373946dea98fa5c362`，候選產品 SHA 為 `c493b7315d0cd3b16014add96af969c49ebf4660`。新基底含 root 的精確 free-end 單行維護；本候選相對它仍只有三個 leaf 差異。首版 a048／F4f 的固定權威與原件留作歷史，不把其結果或舊 #288 綠燈挪作本候選驗收。

## 目前成本與範圍

`contact_world.c` 已有每次查詢建立的 `ContactOrderIndex`：完整 32 位 ID 比對，排序讀最後一筆順序，遮蓋判斷讀最小順序；超過現有成員容量時保留線性後備。`geometry-core/kernel/source.c` 已有 node/edge 索引與 hint。這次不重做這些索引，也不把舊草稿的線性查找預測當現況。

每次 `wood_contact_collect_stops()` 仍有兩個不同成本：member tail 的穩定 insertion sort，以及擋面去重的候選配對。呼叫次數隨整個工程驗證流程增加，是另一個尚未量測的來源。候選只消除一般去重路徑每刪一面就搬移整段 tail 的成本，不改呼叫次數、不宣稱配對掃描的最壞 O(F²) 已解決。

## 候選算法與等價理由

1. 原收集、原容量截斷、原穩定排序均不動。
2. 收集數量不超過既有 `WOOD_CONTACT_FACE_CAPACITY` 時，在固定大小的局部 bool 陣列記 active 狀態。依原順序訪問每個原始擋面；候選遮蓋者只讀當下 active 的面，原完整座標、重疊、earlier 與完整涵蓋條件均不動。
3. 刪除改為停用目前的面；所有判斷完成後，只將存活記錄穩定壓緊一次。
4. 公開 API 可接收超出內部標準容量的 caller buffer。數量超過既有容量時，保留同一迴圈的原 `memmove` 後備，不新增 heap、拒絕或錯誤碼。

歸納對應：在處理第 k 個原始面之前，原陣列等於候選 active 面的穩定投影。兩者可供遮蓋判斷的面、順序及原事實相同，故同時刪除或保留目前面；完成後回傳數量與前 n 個完整記錄相同。回傳 n 以後但原收集範圍以內的舊資料不是輸出；仍保留原收集範圍以後的 caller tail。

不能先對全部面計算刪除標記：公開 W 事實允許重複 ID，min/last 順序可造成互相遮蓋。兩筆同 ID、順序 1/2、相同矩形會得到四個面；原程式逐一刪掉第一對，最後一對應存活。若停用面仍能遮蓋，或批次預先刪除，會錯成零面。

## 正反例與撤回計畫

| 項目 | 原裁判及必要結果 | 狀態 |
|---|---|---|
| 舊 W 接觸套件 | 全部舊方法、舊具名 ASSERT、舊 controls 保留 | UNRUN |
| 重複 ID 互相遮蓋 | 同 ID 四面逐次去重後恰留最後一對；回傳兩面欄位與 tail sentinel 精確 | UNRUN |
| 超標準 buffer 後備 | 超過既有 face capacity 的公開事實仍回傳同樣兩面，保留 caller tail | UNRUN |
| 停用面不可再遮蓋 | 撤回 active 檢查：基準 0／原具名 ASSERT 1／恢復 0 | UNRUN |
| 穩定壓緊只複製 active | 反轉 active 條件：基準 0／既有 earlier-full-cover ASSERT 1／恢復 0 | UNRUN |
| 回傳存活數量 | 撤回刪除時遞減：基準 0／原重複 ID ASSERT 1／恢復 0 | UNRUN |
| strict overlap | 撤回兩個非重疊條件：基準 0／零長度面具名 ASSERT 1／恢復 0 | UNRUN |
| 完整座標 | 撤回為 32 位座標比較：基準 0／相差 2³² 的不同平面具名 ASSERT 1／恢復 0 | UNRUN |
| 完整優化撤回 | 應與原算法語意等價，故語意裁判應仍綠；只作操作計數對照，不冒稱語意突變被殺 | UNRUN |

每個新 control 必須唯一命中產品碼，編譯失敗、crash、timeout 不算被偵測。保留既有 partial-shadow 的唯一原錨點，避免既有 control 只測到後備而漏掉新路徑。沒有新增全帳本 ID；`tests/mutate.py`、全帳本與 `run_all.expected.json` 由主代理統籌，正式合流時本套件方法數需由 9 更新為 10。

## 保護範圍與後續

不改 SSOT、決策佇列、Reading A、RC 剩餘裸露連續段、成員／擋面容量、16 MiB stack 契約、現有排序鍵及錯誤順序。不刪測試、不改任何舊斷言或原 timeout。不採用舊草稿的 2 MiB、30 秒或其他新通過門檻。

`WoodCutList.groups[C]` 內各有 `ids[C]`，仍為平方儲存；這次不改 public cut-list representation。後續可考慮單一 IDs 區域與 group offset，先保 ID 宣告順序、分組排序、POD 複製及 C/C+1 原子拒絕。

操作計數可分開觀測 sort 比較／搬移、dedup 配對／搬移、source probe、cut-list group 比較／整組 swap。觀測只報真值與等價結果；任何新數值 pass/fail 門檻列入 QUESTIONS，不推定已核可。
