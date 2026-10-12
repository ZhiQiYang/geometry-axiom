# GEO-258 候選退役狀態與 archive 重驗

受測來源 commit `b7d2f8d5a5097f8f7d9f90054228b896945e8f0c`；本次證據提交只補本紀錄及新突變結果，不更動受測產品或測試來源。2026-10-12 經 WSL v3 排隊鎖執行，保留全部子命令、退出碼、耗時、來源／二進位指紋、失敗與還原日誌。

## B1 修正

候選內已刪卡片的退役集合屬於該 World 候選。取消、操作失敗、幾何重驗失敗、確認後 Undo、唯讀驗證及載入失敗不會污染後續候選；成功 batch 與互動 archive 結束會清除暫存集合，不寫入 dump。六個新增跨入口案例均先驗正式世界不變，再實際進行後續 archive 修改預覽。

第一輪 `18a0d28fd955921510cae8a8a2d7f1c0fa0044bd` 的參數 suite 實跑 23 題，22 通過、1 失敗：後續 archive 寫入 6，讀取卻是未求值的 0。據 I8／I38 補上互動 archive 成功後的參數及完整依賴重驗，保留精確診斷；場景載入仍延後至讀完整份檔案才重驗。新增案例檢查相依 datum、正式值、Undo／Redo，以及缺引用／除零／幾何非整數的原子拒絕。兩個新增 archive 方法在修前和移除重驗的突變中均實際失敗。

## 實跑範圍

| 定向測試 | 實跑方法數 | exit | 秒數 |
|---|---|---|---|
| baseline-test_parameters_core | 25 | 0 | 7.257 |
| baseline-test_section_profile_native | 28 | 0 | 13.602 |
| baseline-test_assembly_rules | 36 | 0 | 6.897 |
| baseline-test_evidence_link_native | 6 | 0 | 1.934 |
| baseline-test_engineering_core | 18 | 0 | 4.996 |
| baseline-test_assembly_parameter_refs | 3 | 0 | 1.586 |
| baseline-test_engineering_model_sources | 4 | 0 | 2.487 |
| B1-extra-green | 6 | 0 | 1.482 |
| restored-focused-green | 7 | 0 | 2.289 |
| B1-extra-restored-green | 6 | 0 | 1.486 |


另執行 integrity、既有核心場景與 bridge 場景完整性；退出碼均為 0。舊版 `7b603b4dc34bbbf41731f0e7845d0519dd876c71` 套用同一回歸測試後重現作用域污染，未以程式啟動錯誤或略過當突變成功。

13 個定向突變皆觸發行為斷言，每次突變結束都逐位元還原來源；全部完成後再重建 bridge，重跑 7 題聚焦與 6 題 B1，均為綠。每次 bridge 都記錄 sidecar 與實算執行檔 SHA-256，不宣稱每個突變後都有獨立基線實跑。全表 50 筆：42 killed、1 crashed、4 equivalent、3 retired；`mutate.py --check` exit 0。crashed 單獨列出；新來源閉包與裁判指紋已更新。

本輪 114 次取樣無外來程序。收據與原始輸出位於本次 scratchpad 的 `board-local-codex/pr193-proof-b7d2f8d5-r2/`；首輪 archive 失敗保留於 `pr193-proof-18a0d28f/`。中間一輪 `pr193-proof-b7d2f8d5/` 的 assembly-parameter-refs 匯入因私有 clone 不在 PYTHONPATH 而失敗，未算作產品反例或成功證據；這一輪明確帶入每個 clone 的 PYTHONPATH 後重跑，兩份失敗原件都保留。本次未新增 UI 入口。

## 仍待處理

M1 的 P-060 裁決已於 6113538272 核准：引用檢查以完整最終候選為準，退役 id 在同一候選仍不得重用。本次受測產品尚未實作該修正，因此 M1 仍是阻擋，不以 B1 通過解除。delete/delete 與 delete/put-literal 雙順序案例已另備；delete 在前、明示 unbind-source 在後時如何取得被刪來源的當下值，已在 6113791011 請 Claude 補明，不自行暗凍結仍有的引用。標準 native 與六個瀏覽器 job 尚待修正後 head 的正式裁判；#192 已另交正典同步 e37c068，下游仍須按唯一整合順序承接。CI 受帳號計費阻擋，以本機 WSL 收據代替。本次為定向驗證及核心全表突變，不是七 job。


## Net-zero R5：候選暫存與參數值 padding（2026-10-12）

本段受測產品與測試來源為 `d8111e795c23bcfe7feb59e309a1fee0e6e0c6b4`；此後的帳本／文件提交不更動受測產品或測試。上述較早來源的作用域與 archive 收據保留為歷史，不移作本段新來源裁判。

空候選新增後刪除參數卡、同候選多個退役 ID、互動 archive 之後的空變更，以及保存後冷／暖 bridge 四個案例，原來源 `95871beaba2e6cf2a2aa8f21b74105775fada464` 均實際失敗。dump 相同仍會增加 revision／history，其中實際 redo 被丟棄、undo 落到隱藏空歷史；不是執行器啟動錯誤。

兩個成功出口現在清除整個 `parameters.retired` 陣列，再歸零 count，讓暫存身分不進入候選比較／已提交快照。參數求值改成先清零 `ParamValue`，再逐欄寫入 num／den／unit，消除已量測到的 cache padding 差異。沒有修改 World comparator、定義序列化、既有測試期望或 P-060；不以降低 oracle 來接受空變更。

R5 在同一輪先得到四題舊碼紅燈，修正後四題綠燈；8 個既有模組共 126 題、130/130 integrity、143/143 原生場景也全通過。4 個反證如下，每個都實際觸發指定行為斷言，來源與 bridge 重建後四題完整回綠，最後再驗四題全綠：

| 反證 | 撤回內容 | 觀測 |
|---|---|---|
| M1 | batch 只歸零 count | 四題失敗 |
| M2 | archive 只歸零 count | archive 後的 undo 指向錯誤世界 |
| M3 | batch 只清第一個 retired slot | 多 ID 候選丟失既有 redo |
| M4 | cache 恢復整個 struct copy | 相同保存定義的冷／暖候選增加 history |

R5 實際 v3 外層 exit 0；33 個完整子命令日誌逐檔核對 SHA-256，25 次程序採樣的 foreign 集合為空。原件在 `board-local-codex/pr193-netzero-proof-r5/`，收據 SHA-256 `6ee1c2f8d5ba8db83c0c65f6d8b026748b8aa2cd2cbf8cc82c3539d4756015ab`。先前 R3／R4 與逐 byte 診斷保留原紀錄，沒有改寫為成功。

提交產品後另從 `d8111e795c23bcfe7feb59e309a1fee0e6e0c6b4` 乾淨 clone 重編 core／integrity／bridge／model-base，4 題 net-zero 先過；更新全部 50 筆變異帳本，得到 42 killed、1 crashed、4 equivalent、3 retired，`mutate.py --check` exit 0。其後 parameters 25、retirement 6、net-zero 4，共 35 題再次通過。四支執行檔的實算 SHA、sidecar 與 fresh 狀態在工作前後一致，來源未改，70 次程序採樣 foreign 為空。這一輪實際外層 exit 0；原件在 `board-local-codex/pr193-netzero-final-native/`，帳本 SHA-256 `43dd741cad076518be38599df6ff669066c624bf4ce59cefd0dc7f8fd673c531`。

這是 WSL 定向驗證及核心全表變異，沒有新增七 job 收據。P-060 的最終候選引用檢查尚未實作，明示 unbind 取值仍等候 Claude 裁決；正典跨線整合與最終七項仍須後續驗收。GEO-219：無新入口。CI 受帳號計費阻擋，以本機 WSL 收據代替。
