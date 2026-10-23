# 現版基線與權威

基底為公開 train `a048530c18f5df43a921e6b06bb3e4aa2192684e`，fresh main `425c092eaf16f90256d76433243baebde45163ac`，fresh handoff `e91e8e0c82afd9ae784e25fe63566f3e42f4b2d4`。原權威讀取指令、Git 退出碼、完整輸出與環境存於 `AUTHORITY_ORIGINALS.tar.gz`，逐檔 inventory 及封包往返檢查另列 JSON。原始 clone 只有先前記錄的 exit 0 與完整指令文字，沒有事前 c387 收據；不補造事前記錄。

| 權威或參考 | 原始 bytes SHA-256 |
|---|---|
| train 決策佇列 | cfad2b7ad5181a97a0d87e0791f96548cb0838f6222a01fabdf06d987b5211e0 |
| main 決策佇列 | a9f14cdd3cf2846c65d0a7cc32f02bf3a12ba60e817cd9223c59e4da6f4734e5 |
| 公理層，LF | c66c48e50e0caceef42721c79700365f090f5c48d297abba41993eeb40dba9b7 |
| FIELD-RULES | 3305d8000af9814b91c2646cfcbbc841e1ead813fe3390e482f8bfc2a71c0ab2 |
| 舊 issue300 DESIGN | 06f09369ece61f7f977a34cbfcaef28953da7e6b91f0e038a0b0f80c6f29dfdd |
| 舊 issue300 TESTS | c727cb26bbcc596650dc364ef3ea72e594929fd8864de45b940dbbf2fb11196c |
| 舊 issue300 bench README | 8d83880aab16091e88272437b8985e08e7ec30987b39a30ab47d2646848acd72 |

已讀 10/12～15、10/22、10/23、10/24 指定決定；train 這整份決策佇列、公理與 FIELD-RULES 和先前已讀原件逐位元組相同。權威與舊草稿分開：FIELD-RULES 的整理不取代公理；舊草稿的 09ab/603e 基底、容量 512、2 MiB 或 30 秒不當本次已採納條件。10/24 的 RC 規則使用「剩餘裸露連續段」，不覆蓋成舊整段 RC 面規則。

| 五個現有容量定義 | 值 | 位置 |
|---|---:|---|
| WORLD_MAX_TIMBERS | 64 | current_geometry.c |
| WOOD_MEMBER_CAPACITY | 64 | native/document.h |
| WOOD_CONTACT_MEMBER_CAPACITY | 64 | native/contact_world.h |
| WOOD_CUT_LIST_MEMBER_CAPACITY | 64 | native/cut_list.h |
| WOOD_MEMBER_SPAN_MEMBER_CAPACITY | 64 | native/member_reference.h |

五者仍各自定義；既有 span ABI 檢查不等於完成五者單一來源。cut-list 每個 group 仍有 ids[C]，共 C² 個 uint32_t 格，C=64 為 4096 格。若直接改 512，單 ID 矩陣就是 1 MiB；這是型別算式，沒有新量到 sizeof(World)，也沒有擴容完成聲稱。

已存在的 `test_geo261_source_index.py`、`test_geo261_contact_sources.py` 分別覆蓋 node/edge 索引與 order index 的 identity、碰撞、fallback、min/last/freshness。`test_geo261_wood_contact_world.py` 原有 9 方法及 18 controls；`test_geo261_wood_report_policy.py` 保 group/ID 順序與 C/C+1 原子拒絕。這些既有裁判不砍掉；本次候選只在原 W 接觸套件新增一方法及五個 control，正式 expected count 待主代理合流維護。

本分支沒有新的原生、瀏覽器、效能或全帳本結果。完整帳本仍由主代理在 F4f 執行，不能當本候選驗收。
