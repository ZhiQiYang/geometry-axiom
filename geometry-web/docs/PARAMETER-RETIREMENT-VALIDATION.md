# P-121／P-122／P-129 候選狀態（2026-10-15；尚未執行本輪驗證）

[P-121](https://github.com/ZhiQiYang/geometry-axiom/pull/193#issuecomment-6179914302) 要求引用者在來源最後一次刪除後明確重新宣告；同鍵重建不自動處理舊引用。[P-122](https://github.com/ZhiQiYang/geometry-axiom/pull/193#issuecomment-6180612542) 已撤回 P-117 的匯入跳號：配號維持 R53，剛刪鍵可被匯入重用，安全由 I38 引用保護負責。[補充](https://github.com/ZhiQiYang/geometry-axiom/pull/193#issuecomment-6180660038) 同時涵蓋省略 fieldId 的欄位刪除與最後一次刪除。

候選新增欄位刪除事件與各引用者的明確宣告順序，出口清空整個候選暫存；工程來源及覆寫分別處理，格式轉換不冒充改綁。P-062／P-065 的明確解除保留已結束來源的最後有效值；同鍵重佔不得刷新成無關新值。沒有新增 K3 記號、能力或保存格式。

[P-129](https://github.com/ZhiQiYang/geometry-axiom/pull/193#issuecomment-6184120678) 已裁決：刪後相同內容的明確宣告算 I38 改綁，僅涵蓋該操作實際宣告的部分；四類沒有 engineering op 的 DSL 引用者不能靠重建來源放行。本候選新增三個原生回歸方法：四類 DSL 引用拒絕、grid 單軸宣告不處理另一軸，以及預覽只揭露最後刪除後仍存在的明確宣告。既有 assembly／section-profile 正例也核對預覽列出的引用者。

`redeclaredReferences` 隨 engineering／assembly／section-profile／panel-fill 的整包預覽回傳來源欄位、引用者及說明；原生序列化使用離開候選前的操作順序副本，正式 World 先清空暫存，再做完整重驗。序列化後即釋放順序副本，不進入 World、history、交換格式或確認令牌。刪後重宣告說明併入各工作區既有影響清單。Python 與 JavaScript 目前僅通過語法檢查；原生編譯、定向測試及新真突變仍待實際執行。

已改自己的匯入配號與 P060 順序測試，恢復 R53 期待的 0／1／2；加入七個回歸方法，涵蓋卡片、欄位、最後刪除、重宣告前後順序、未刪與從未存在的欄位、工程 base／override 分離，以及重建後明確解除的最後有效值。main K2a、SSOT、白話與正典未修改。這些只是已寫出的測試，**尚未執行，不能算通過**；run_all 的新方法數仍待實際執行後同步。

WSL 最新順序依 P127／P128：Chrome 啟動診斷核定後，train16 固定 `6a62bb05` 單獨 grid 一次；train15 已退役，不再重跑。P129 解除本候選對相同引用重宣告的規則解讀阻擋，修正後仍須定向原生及新真突變。舊 P117 R1／R2 僅等鎖即撤回，舊證明與舊 train17 控制保留 HOLD，不得執行；沒有借歷史 150 題或舊突變結果替本候選背書。Claude 審查通過後才可與新 #237 組核心鏈第17班；最終整合來源仍須全新完整帳本、官方 sync／check／原41 與固定最終 head 七項。

K3「同鍵重建配新記號」及「沿用舊記號突變轉紅」兩項依 P117 其餘裁決仍移交 K3-L／GEO253；本 PR 沒有實作或宣稱通過。

## 下列為 P121／P122 前的歷史實測

歷史原文保留；其中「重建鍵即可接回舊引用」已被 P121 否決，舊 P111 的兩個突變不能驗收本候選；舊 P117 匯入跳號與對應測試也已撤回。下列綠燈只屬各自列明的歷史來源。

# GEO-258 候選退役狀態與 archive 重驗

最新狀態（2026-10-15，P-111 現有路徑修正已定向實測）：[P-111](https://github.com/ZhiQiYang/geometry-axiom/pull/193#issuecomment-6173105491) 以 D60／R56 更新 P-060 的「不重用身分」：退休的是舊存在期，不禁止同候選重建同一個鍵。put／import 已移除鍵保留限制，最終引用檢查只拒絕仍缺失的來源；自己的舊反例改驗合法重建、完整候選與中間刪除收據。main 的 K2a 測試與 SSOT 未修改。

受測乾淨來源 `886727a2649091158634afb1712915a8a3980d5c`（產品修正 `b032f48d4fe98197f803b0144a6a97f8f13c1763`）；之後的提交只同步工具生成的唯一正典及本紀錄，沒有改受測產品／測試。實際 WSL exit0、150 題真 bridge／相依 Python 方法全過，完整原生場景 143 項與 integrity 130 項通過；原位 sync→--check→原41 全部0。四支固定執行器前後實算 SHA 相同且 fresh；來源、binary、sidecar、每步原日誌由另一個只讀驗證器核符。

兩個真反證皆先實際失敗1題、逐 byte 還原並重編後指定2題回綠：恢復舊鍵退休拒絕使未改的 main K2a 轉紅；把已重建鍵誤當缺失來源使自己的存活引用重建案例轉紅。它們只證明現有交易路徑，**不代替尚未實作 K3 的舊記號沿用反證**。全表變異帳本與固定最終整合 head 的正式七項仍留下一班依 P-109 執行，不借舊綠燈。

本輪原件：`D:/geometry-axiom-work/board-local-codex/pr193-p111-native-r2`；收據 SHA-256 `3d401eccd6437d293ec12231ba72e0b20310d3c1b74a59db75e339f707e36839`；完整獨立讀回 `D:/geometry-axiom-work/board-local-codex/pr193-p111-native-r2/independently-verified.json`。外來程序僅取樣、集合為空：`{"samples": 133, "foreign_processes_seen_during_run": {}, "exclusive_during_run": true, "max_loadavg_1min_sampled": 7.31}`。共享四 runner 同 SHA；未觀察隱藏啟動器最終 OS exit，保持 unknown。R1 僅在等待鎖時撤回（實際 WSL9，未 checkout／編譯／測試），原件在 `pr193-p111-queue-r1`；R2 未覆蓋它。

| 實際步驟 | 原 exit | 秒數 |
|---|---:|---:|
| clone | 0 | 4.789 |
| checkout | 0 | 336.915 |
| fixed-build | 0 | 161.848 |
| fixed-test_parameters_core | 0 | 106.699 |
| fixed-test_parameters_final_candidate | 0 | 20.284 |
| fixed-test_parameter_retirement_scope | 0 | 27.203 |
| fixed-test_parameter_netzero | 0 | 23.315 |
| fixed-test_parameters_unbind_scope | 0 | 35.884 |
| fixed-test_parameters_deleted_unbind | 0 | 63.676 |
| fixed-test_parameters_upstream_unbind | 0 | 56.208 |
| fixed-test_parameters_candidate_value_history | 0 | 55.646 |
| fixed-test_grid_system_contract | 0 | 67.126 |
| fixed-test_engineering_core | 0 | 80.778 |
| fixed-test_assembly_parameter_refs | 0 | 35.443 |
| fixed-test_engineering_model_compatibility | 0 | 16.892 |
| fixed-integrity | 0 | 3.497 |
| fixed-core-scenes | 0 | 14.682 |
| M1-restore-key-retirement-build | 0 | 46.892 |
| M1-restore-key-retirement-red | 1 | 7.84 |
| M1-restore-key-retirement-restore-build | 0 | 43.229 |
| M1-restore-key-retirement-restored | 0 | 15.471 |
| M2-treat-rebuilt-source-as-missing-build | 0 | 43.313 |
| M2-treat-rebuilt-source-as-missing-red | 1 | 7.896 |
| M2-treat-rebuilt-source-as-missing-restore-build | 0 | 42.818 |
| M2-treat-rebuilt-source-as-missing-restored | 0 | 15.819 |
| reader-sync | 0 | 11.513 |
| reader-check | 0 | 1.929 |
| reader-forty-one | 0 | 382.847 |


目前 K3 正式契約明寫核心／宿主／保存尚未實作，原生核心沒有 `identity-ledger/1` 啟用與記號路徑。[驗收範圍缺口](https://github.com/ZhiQiYang/geometry-axiom/pull/193#issuecomment-6173502544) 已回報；本次不造記號，不宣稱新 incarnation 或沿用舊記號反證通過。下列舊紀錄中「同候選禁止重用鍵」及其反證只屬當時 P-060 的歷史結果，已由 P-111 取代；完整候選引用驗證、暫存隔離及 P-062／P-065 最後有效值的既有要求仍保留。

前次狀態（2026-10-14）：P-065/B5 已補候選覆寫前的最後有效值，產品／測試提交 `69eb637552d0f5616d044a3116ea18ecb5077439`。同份12新題修前8行為斷言紅／4對照綠，修後連同既有26題共38綠；27／29等六組完整dump雙序逐byte相同，兩個針對覆寫捕捉／刷新的真突變及新鮮全50帳本詳文末。B3 最終 #207 整合與 B4 固定最終head的正式七項仍待，不宣稱整個PR已完成。

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

八題修後全過；10個相關模組134題、integrity130/130、核心場景143/143亦過。新正向案例各驗 preview不改dump/revision、cancel無變動、confirm一次history、完整Undo/Redo；負向案例各驗無效preview不能confirm、正式dump/revision不變且既有redo保留。依賴由27改29、覆寫由29改31後，解除綁定保存新整數值；覆寫案例的原始來源仍為27。既有測試期望未改。

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


## P-062：已刪參數卡的明確解除綁定（2026-10-12）

依裁決6123283405及審查6123850524：已刪來源取同候選刪除前最後有效值，包含先前修改；存活來源與覆寫依當下依賴求值。只在明確 unbind 時消費暫存，最終仍懸空的引用依P-060整包拒絕並指名。一般求值器不讀刪除暫存，沒有每次刪除的全圖rebuild。

同一份14題在未改產品的 `738d45a0bfec91a204f07419ebc8041a78a2874b` 上先跑，11題紅、3個對照綠；前測實際外層exit0只表示預期紅燈驗證完成。修後14題全綠：雙順序dump逐UTF-8位元組相同；來源或傳遞依賴改27→29後取29；來源刪除後不追後續依賴變動；存活覆寫取31、已刪覆寫保留29；雙來源刪除、取消、失敗、跨候選重用身分與Undo/Redo均按原生bridge觀測。未明確unbind、分數幾何與存活來源缺依賴仍拒絕。

首輪修後工作7191實際exit1：14新題、integrity130及場景143已過，但既有25題中 `test_matrix_explicit_unbind_then_delete_is_one_transaction` 仍把P-062已採納的delete-before-unbind期待為無效；實際valid為true，故其舊assertFalse失敗。停止後僅依P-062更新該方法，增加取消、revision單增、雙順序dump同一與Undo/Redo；直接刪除而不unbind的拒絕斷言保留。AST核對其餘既有方法不變，既有expected數目亦不改，只新增14題項。原失敗輸出與receipt保留於 `pr193-p062-after/`；產品來源及14題新測試未變。

第二輪在全新clone執行：14新題及11個既有模組142題全過（其中上述1題明確按裁決更新），另有130/130 integrity與143/143核心場景；沒有skip或ERROR。

| 定向步驟 | exit | 秒數 |
|---|---|---|
| fixed-fourteen-green | 0 | 3.279 |
| fixed-test_parameters_unbind_scope | 0 | 1.826 |
| fixed-test_parameters_core | 0 | 6.789 |
| fixed-test_parameter_retirement_scope | 0 | 1.325 |
| fixed-test_parameter_netzero | 0 | 1.076 |
| fixed-test_parameters_final_candidate | 0 | 1.327 |
| fixed-test_section_profile_native | 0 | 14.823 |
| fixed-test_assembly_rules | 0 | 6.94 |
| fixed-test_evidence_link_native | 0 | 4.433 |
| fixed-test_engineering_core | 0 | 4.734 |
| fixed-test_assembly_parameter_refs | 0 | 1.426 |
| fixed-test_engineering_model_sources | 0 | 2.63 |
| full-mutation | 0 | 1240.726 |
| final-fourteen-green | 0 | 3.381 |

三個行為突變各以新bridge實跑：移除刪除暫存→delete-before-unbind無有效值而遭拒；跳過刪除前依賴求值→確認後錯存27而非29；省略暫存清空→下一候選重用卡片身分後錯存27而非31。每項失敗命中指定行為斷言，逐一還原來源、重編bridge後14題全回綠，不把編譯或啟動失敗當killed。

原生閉包改變後完整重跑50筆帳本：42 killed、1 crashed、4 equivalent、3 retired；沒有stale、survived或blocked。WSL與Windows `mutate.py --check`均通過。帳本SHA-256 `efe6a88ddc93769265f6cb9deaeb926bb9658569b03be658a1cbdfb4660593f8`。帳本後14新題＋47既有題共61題再過。

受測輸入為 `738d45a0bfec91a204f07419ebc8041a78a2874b` 加八個凍結產品／測試路徑，實跑時並非乾淨提交；提交 `c9ad24fbf957eb23f0ec7bf23adea4531d9db7a1` 的八路徑已由Git逐份讀回，LF SHA全部等於受測來源。契約文案另更新。四支二進位實算SHA前後相同且fresh，完成輪實際外層exit0，102次取樣foreign空；收據SHA-256 `780eea8735d09db3bbe21bfa8ff4020f57f6a55c5a9d649b8f40435526445be5`。完整原件位於scratchpad `board-local-codex/pr193-p062-before/`、`pr193-p062-after/`及`pr193-p062-after-r2/`。

具體多來源邊界仍待Claude裁決（https://github.com/ZhiQiYang/geometry-axiom/pull/193#issuecomment-6124416895）：D=27、S=@D且目標綁S。unbind→delete D→delete S的preview有效為27，D先改29時為29；delete D→delete S→unbind的兩種preview均被拒。四組皆preview→cancel，dump回應與revision不變，未confirm。診斷原件15路徑已公開並獨立GET核回，未將此待決案例列為已完成正向驗收。

B3依裁決由最終#207整合owner在承接後原位sync→check→原41題；本輪未改SSOT、白話、閱讀器、AXIOM常數、BACKLOG或決策佇列。B4最終七job仍待，不把本輪定向與變異當七項裁判。GEO-219無新入口；CI受帳號計費阻擋，以本機WSL收據代替。


## P-065：上游先刪時的最後有效值（2026-10-14）

依裁決6125213098及審查6125569301採A：只有來源自身也已刪且明確unbind可讀候選暫存；仍存活的來源／覆寫依當下依賴驗證。刪除時先找受影響的引用路徑、重算其必要欄位並更新最後有效值，不在每次刪除重建全圖，也不讓一般求值器讀暫存。原候選出口清零與最終懸空拒絕保留。

同份12新題先在未改產品的 `86d3e0e376fe6dcc90936dd5e2ef301339f0b1d5` 上實跑：8題是缺少同候選有效值的行為斷言紅燈，4個對照原本就綠；然後才在該測試clone套入五個凍結路徑。修後12新題與原P-062的14題合計26題全綠，既有測試期望不改。另有11個既有模組142題、130/130 integrity及143/143原生場景全過。

四組實際bridge確認原件保留所有命令、請求JSON、回應、完整dump、revision、取消及Undo/Redo。D=27、S=@D時，unbind→delete D→delete S與delete D→delete S→unbind都得到27；同候選先改D=29，兩序都得到29。兩組完整dump各自逐UTF-8位元組相同。第五組原件驗證D刪但S存活，unbind使整包無效、confirm被拒、正式dump與revision不變，診斷指名S→D。來源存活／覆寫存活、傳遞來源、無關循環、雙來源、來源恢復後的新值31、失敗候選不洩漏及0號卡片／欄位也在12題內。

| 定向步驟 | exit | 秒數 |
|---|---|---|
| fixed-twenty-six-green | 0 | 104.038 |
| confirmed-value-traces | 0 | 21.969 |
| fixed-test_parameters_unbind_scope | 0 | 32.176 |
| fixed-test_parameters_core | 0 | 99.822 |
| fixed-test_parameter_retirement_scope | 0 | 25.624 |
| fixed-test_parameter_netzero | 0 | 22.78 |
| fixed-test_parameters_final_candidate | 0 | 17.936 |
| fixed-test_section_profile_native | 0 | 157.265 |
| fixed-test_assembly_rules | 0 | 268.961 |
| fixed-test_evidence_link_native | 0 | 45.505 |
| fixed-test_engineering_core | 0 | 140.263 |
| fixed-test_assembly_parameter_refs | 0 | 68.487 |
| fixed-test_engineering_model_sources | 0 | 83.783 |
| full-mutation | 0 | 3823.118 |
| final-twenty-six-green | 0 | 94.822 |

M1移除上游失效前的捕捉，原值與先改29的兩個upstream-first案例實際斷言失敗；M2不更新已有暫存，來源恢復後應取31卻錯取27而失敗。每項逐byte還原產品、重編bridge後26題全部回綠，沒有把編譯或程序啟動錯誤當成突變被測到。

原生閉包變動後刷新全表50筆：42 killed、1 crashed、4 equivalent、3 retired；無stale、survived或blocked。WSL與Windows的`mutate.py --check`均通過，帳本SHA-256 `b436d97c63886d11e85fc7ab6b4727a47614859a253e9e9720503dec6f28da0c`。帳本後26題及47個既有參數案例共73題再通過；固定四支執行檔的SHA在工作前後一致、sidecar皆fresh。

受測輸入是 `86d3e0e376fe6dcc90936dd5e2ef301339f0b1d5` 加五個凍結路徑，實跑時不是乾淨最終提交。提交 `45013ece5147d4d5c1bad2de35387d2bdfaf28c8` 的五路徑已從Git讀回、LF SHA逐一等於受測輸入；契約文案另更新。同一性核對沒有宣稱另一次產品實跑。實際WSL exit0（隱藏launcher的OS退出碼與外層工具退出碼未獨立取得），489次取樣foreign空；收據SHA-256 `cb15882b36dc8aaf179ecb96fb628191a60fe756a2201f47a1d6b980f7f4c99b`，五例原件SHA-256 `e682e84bcfd97339f61cded5d0fd16f5e27691aa9f58a2e1299e5255e272789b`。完整來源、首跑、突變、還原、帳本與原始輸出保存在`D:/geometry-axiom-work/board-local-codex/pr193-p065-native-r3/`。

P-062末段的「多來源邊界待裁」是當時狀態，已由本段P-065裁決與實跑承接；原15份反例和111份P-062交付原件保留原版本界線。B3最終#207正典整合與B4正式七job仍待；本輪無新UI入口，未改SSOT、白話、閱讀器、AXIOM常數、BACKLOG或決策佇列。CI受帳號計費阻擋，以本機WSL收據代替。


## P-065/B5：覆寫成暫時缺引用前的最後有效值（2026-10-14）

依審查6166398934及既有P-065採A，`D4=27、S3=@4:1、T→S3` 在同候選先把D4改成缺失引用，再刪D4／S3並明示unbind，仍保留27；先合法改成29再改壞則保留29。修正只在合法語法／容量檢查後、真正覆寫既有卡片前，沿原受影響閉包刷新暫存。一般evaluator及存活來源／覆寫不讀暫存，最終引用與候選出口清空閘門不變，未改SSOT。

同一份12新題先在乾淨 `842db122a58cc25c048234f52314498a0d09dc05` 的產品跑：8個行為斷言紅、4個對照綠；其後才在測試clone套入四個凍結路徑。修後既有P-062十四題／P-065十二題與B5十二題共38綠。六組真bridge確認的27／29、循環、欄位移除與無關非法中間態，完整原生dump雙序逐UTF-8 byte相同；也驗取消／失敗不洩漏、存活來源及override仍拒絕失效依賴。

M1拿掉覆寫前捕捉，兩個指定27／29案例以missing有效值斷言紅；M2只允許第一次捕捉，29案例實得27而紅。每項逐byte還原、重編，再跑38題全綠。另有既有11模組142題、integrity130／130、核心場景143／143。全50帳本重新產生：`{"killed": 42, "equivalent": 4, "crashed": 1, "retired": 3}`，無stale／survived／blocked；原執行檔與sidecar均封存。Windows另作來源／裁判帳本校驗，不冒稱再跑mutants。

| 原步驟 | 實際退出碼 | 秒數 |
|---|---:|---:|
| fixed-thirty-eight-green | 0 | 166.741 |
| fixed-integrity | 0 | 2.537 |
| fixed-core-scenes | 0 | 12.783 |
| fixed-test_parameters_unbind_scope | 0 | 36.03 |
| fixed-test_parameters_core | 0 | 107.887 |
| fixed-test_parameter_retirement_scope | 0 | 28.179 |
| fixed-test_parameter_netzero | 0 | 25.527 |
| fixed-test_parameters_final_candidate | 0 | 20.757 |
| fixed-test_section_profile_native | 0 | 169.375 |
| fixed-test_assembly_rules | 0 | 167.574 |
| fixed-test_evidence_link_native | 0 | 32.783 |
| fixed-test_engineering_core | 0 | 80.341 |
| fixed-test_assembly_parameter_refs | 0 | 33.063 |
| fixed-test_engineering_model_sources | 0 | 12.688 |
| M1-no-pre-overwrite-capture-red | 1 | 12.265 |
| M2-no-pre-overwrite-refresh-red | 1 | 8.301 |
| full-mutation | 0 | 1372.758 |
| mutation-check | 0 | 6.617 |
| final-thirty-eight-green | 0 | 170.918 |

完整原件：`D:\geometry-axiom-work\board-local-codex\pr193-b5-native-r1`；receipt SHA `5453d2c84645f997b38c9dfc74ee33e4388e3c802017c50b155dd58238a9867a`，帳本 SHA `d24c8b8cf2f3587373a8f3048c3f56d21ff44576d74e97d9fcb97d430187e959`。實際WSL exit0；hidden launcher的OS退出與外層工具退出未獨立取得，保持unknown。foreign原取樣清單空，不宣稱連續監看。受測是乾淨842db加四路徑凍結overlay；提交後Git讀回只核同一性，不把它改標為乾淨final SHA重跑。B3／B4仍由既定最終整合及正式列車承接。舊P-060／P-062／P-065各輪失敗與原退出碼全文保持。
