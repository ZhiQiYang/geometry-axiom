# GEO-258 候選退役狀態與 archive 重驗

最新狀態（2026-10-12）：獨立來源的 unbind 已改為重算其必要的當前參數依賴，產品／測試提交 `426629ff8050b2ee6eb7444f70554d47f729b8b4`；無關卡片 delete/unbind/delete 三排列、取新值、覆寫與原子拒絕均有真 bridge 證據，詳見文末「P-060：獨立來源解除綁定」。先前卡片雙順序與 net-zero 核收保留。刪除被綁來源後的取值政策、跨線正典整合與最終七 job 仍待完成。

以下各批次保留當時的來源與結果；較早段落中的「本次」僅指該批次。

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


## P-060：卡片引用依完整候選檢查（2026-10-12）

P-060 裁決來源為 6113538272；net-zero B1 的既有 ce28fdb 範圍已由 6119590300 限定核收。以下是新的卡片順序修正，沒有把舊 R5 或舊帳本當成新來源通過。

舊碼 `ce28fdb550f7630b8e54b45ffcddd808af28a873` 在真 bridge 上先跑同一份四案例：刪來源再刪依賴卡、刪來源再把依賴卡改直接值兩例失敗；反向刪除與最終懸空拒絕兩例通過。工作6939實際外層exit0，4次取樣foreign空。反向刪除是原先就綠的對照，未宣稱它在逐步守門下會紅。

`parameter_remove` 只刪定義並退休身分；完整 batch 及單行 archive 在清除退休暫存前檢查最終引用。保留同候選不能再宣告退休身分、匯入配號略過退休身分、完整幾何重驗與原子提交。四新案例驗雙順序、preview不改正式World/revision、一次history、Undo/Redo、最終懸空保留redo、兩種重用反例。

受測開始head為 `ce28fdb550f7630b8e54b45ffcddd808af28a873`，另套七個凍結產品／測試路徑；實跑時並非乾淨提交狀態。產品提交 `3c24988517fbc3c3890fb87a77b2c77e1a960b89` 的七路徑經 Git 讀回逐份 LF SHA 核對，與原收據的固定輸入全部一致；契約文案另更新。未把提交後的原碼同一性核對寫成另一次產品實跑。實際工具終態為exit0；收據 SHA-256 `7257187a341d3cc28d52f0ccdad29e9ba1947034ed2db328833cd9e92c30ae68`。

四個新案例、以及9個相關模組的130題全過，另有130/130 integrity及143/143核心場景。既有測試只改一處診斷期望：delete後put同一身分由退休身分守門先拒絕，不能再期待逐步刪除診斷；原子拒絕與dump/值不變斷言保留。既有unbind案例只更正文意註解，合法性期望未改。

| 定向步驟 | exit | 秒數 |
|---|---|---|
| fixed-four-green | 0 | 1.128 |
| fixed-test_parameters_core | 0 | 5.887 |
| fixed-test_parameter_retirement_scope | 0 | 1.123 |
| fixed-test_parameter_netzero | 0 | 0.922 |
| fixed-test_section_profile_native | 0 | 13.068 |
| fixed-test_assembly_rules | 0 | 6.499 |
| fixed-test_evidence_link_native | 0 | 5.0 |
| fixed-test_engineering_core | 0 | 4.032 |
| fixed-test_assembly_parameter_refs | 0 | 1.325 |
| fixed-test_engineering_model_sources | 0 | 2.029 |
| full-mutation | 0 | 887.641 |
| final-four-green | 0 | 0.974 |

四項具名突變均命中指定斷言，每項還原、重編bridge後完整四題回綠：M1恢復每步引用守門→兩個delete-first案例紅，反向刪除仍綠；M2移除最終引用列舉→既定訊息格式斷言紅，但一般完整重驗仍拒絕懸空，且以 `[2:1 dependent.1] -> I38 MISSING: parameter 1 field 1` 指出路徑，僅列為診斷格式反證，不宣稱合法性或引用路徑消失；M3取消put退休限制→重宣告被接受而紅；M4匯入配到退休id後命中put守門，合法匯入preview被錯拒絕而紅，訊息指名parameter 1退休。不把M2宣稱為非法World已提交，也不把M4寫成已提交錯誤id。

變更原生來源後重跑全表50筆：42 killed、1 crashed、4 equivalent、3 retired；無stale、survived、blocked。`mutate.py --check` 在WSL與Windows均通過；帳本 SHA-256 `c02073b6e010a5bbf54ed5cbe357198434254c08219a22e83cc378ba4d6977ed`。其後四新案例、parameters25、retirement6、net-zero4，共39題再過。四支二進位的實算SHA前後一致且sidecar檢查fresh；每次重編時間各自保留。全輪78次取樣foreign空。完整原件在scratchpad `board-local-codex/pr193-p060-before/`與`pr193-p060-after-r2/`。

首輪工作13066的M4產品測試確實失敗，但驗證腳本誤以為會走到配號清單比對，要求不存在的「Lists differ」，因此整輪exit1，未跑帳本。來源已逐位元還原；原始收據、日誌與腳本完整保留在 `pr193-p060-after/`。修正的是突變驗證器的定位：必須同時命中具名測試、independent_import的有效preview斷言及具名退休錯誤。產品、四題測試與斷言未改，第二輪從乾淨目錄重新跑本段全部步驟，未沿用首輪失敗作全輪成功。

界線：delete後才unbind-source應保留何時的尺寸仍等候Claude裁決；本次不實作取值暫存或自動凍結，不宣稱全部P-060完成。正典跨線整合與最終七job未做。上述舊段落各自屬於其註明來源；本段才是此次卡片流程交付。GEO-219無新入口；CI受帳號計費阻擋，以本機WSL收據代替。


## P-060：獨立來源解除綁定（2026-10-12）

本輪處理審查 6120703937、6120894945 的獨立反例：card1=10、card2=@1:1、card3=27，timber1.A 綁 card3；delete1 → unbind → delete2 最終有效，但舊碼在 unbind 全圖重算時被 card2 的中間缺引用擋住。card3 從未刪除，因此不需要裁決「來源已刪後取哪個值」。

先在未修改產品的 `cbe7ca51ec8680dd0c5aef306f63714a5f35be29` 執行同一份八題：中間 unbind、先改依賴再 unbind、先改覆寫來源再 unbind 三題失敗；另外兩個排列、目標缺引用、目標循環、最終無關循環五題原先就通過。前測工作29628實際外層exit0，4次取樣foreign空；三紅均是無關 card2 → card1 導致，不把五個對照寫成修前紅。

`parameters_evaluate_refs` 用全新 DFS 標記、沿用核心 `parameter_eval_field`，重新求值當前原始來源與覆寫的依賴；`eng_effective` 仍驗原始來源與實際尺寸。只把 unbind 的全圖求值換成兩個必要入口，未修改一般 `parameters_rebuild`、候選出口的完整重驗、引用列舉、退役身分不重用或清零。沒有讀舊快取、凍結來源或另建 writer。

八題修後全過；10個相關模組134題、integrity130/130、核心場景143/143亦過。新正向案例各驗 preview不改dump/revision、cancel無變動、confirm一次history、完整Undo/Redo；負向案例各驗無效preview不能confirm、正式dump/revision不變且既有redo保留。依賴由27改29、覆寫由29改31後，解除綁定保存新整數值；原始來源仍為27。既有測試期望未改。

| 定向步驟 | exit | 秒數 |
|---|---|---|
| fixed-eight-green | 0 | 1.825 |
| fixed-test_parameters_core | 0 | 6.042 |
| fixed-test_parameter_retirement_scope | 0 | 1.274 |
| fixed-test_parameter_netzero | 0 | 1.076 |
| fixed-test_parameters_final_candidate | 0 | 0.973 |
| fixed-test_section_profile_native | 0 | 12.567 |
| fixed-test_assembly_rules | 0 | 6.439 |
| fixed-test_evidence_link_native | 0 | 4.435 |
| fixed-test_engineering_core | 0 | 4.034 |
| fixed-test_assembly_parameter_refs | 0 | 1.324 |
| fixed-test_engineering_model_sources | 0 | 1.978 |
| full-mutation | 0 | 865.155 |
| final-eight-green | 0 | 1.674 |

四個行為突變命中指定斷言，逐一還原重編後八題回綠：M1恢復全圖中間求值→三個混合正向案例被錯拒，另外兩個排列仍綠；M2跳過必要依賴求值→錯存舊值27而非新值29；M3移除完整候選world_revalidate→無關循環preview被錯標有效；M4不重算覆寫參數→合法覆寫解除遭幾何整數檢查錯拒。M3與M4均在preview斷言停下，未宣稱它們已提交錯誤World或尺寸。

原生來源閉包已改，重新執行全部50筆突變帳本：42 killed、1 crashed、4 equivalent、3 retired，沒有stale、survived或blocked；WSL及Windows的`mutate.py --check`皆通過。帳本SHA-256 `b6c5bb0b67acb50fffa8015b02bd17e48d42919eea5d281d7697b803b510b55e`。帳本後新八題、parameters25、retirement6、net-zero4、卡片順序4，共47題再通過。

受測輸入是 `cbe7ca51ec8680dd0c5aef306f63714a5f35be29` 加五個凍結路徑；實跑時不是乾淨提交。產品提交 `426629ff8050b2ee6eb7444f70554d47f729b8b4` 的五路徑由Git逐份讀回、LF SHA全部等於受測來源；契約文案另更新，沒有把提交後同一性核對寫成另一輪產品實跑。四支二進位實算SHA前後一致且fresh，全輪77次取樣foreign空。實際外層exit0，收據SHA-256 `1019b8f1c163953db4d089dc01bb695b16950b446303f43b34c7b4da22b0d4ff`。完整原件位於scratchpad `board-local-codex/pr193-unbind-before/`及`pr193-unbind-after/`。

尚待：被綁來源本身先刪除時的取值政策仍等Claude裁決，B3跨線正典／產品整合與B4最終七job未做；本輪是定向驗證及核心全表突變。GEO-219無新入口；CI受帳號計費阻擋，以本機WSL收據代替。
