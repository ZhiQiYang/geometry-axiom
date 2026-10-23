此變更在全部 fact ID 唯一且仍在既有容量內時，將擋面的兩兩遮蓋查詢改成每個完整座標平面的 Fenwick prefix-max 查詢。索引保存單一實際覆蓋面；兩個半面不能合成一個見證。任何 fact ID 重複（包括後來被過濾的 fact）或超容量輸入，仍走原有後備。

基底是 `codex/geo260-ac23-proof-20261024`。本 PR 接續 #341 已做的活集合與一次壓緊前置；原 member insertion sort、重複 ID 後備配對、超容量 memmove 與 cut-list 平方儲存仍在，整個 collector 的平方成本尚未解除。

| 唯一 current-state 矩陣 | SHA／結果與範圍 |
| --- | --- |
| Product SHA | `1ee4e830399b124ebd63c5ff51064d87e53f38d9`；包含產品 `9ee7f98144f81f11385f392e13cc067f1b9d063c` 與真新增方法對應的 expected 10→11 |
| Evidence head | `2a0772da1af26c4da9c7e104fed2a37c760668d4`；僅新增本 PR 的 evidence prefix，產品內容與上述 S 相同 |
| Base | 公開 GEO260 evidence `df230da57619e437c30527dbede8c67fd0ec6b50`；產品 `eb846c345881cc6fc73a53c457a291175365b88c` |
| 靜態驗證 | 凍結草案 157 checks／0 findings；核心 15 機械檢查＋8 語意觀察／0 findings；不可變 Git 來源、expected 與原 push 167／0。各自 scope 限於靜態／Git 證據 |
| 原 wood-contact-world | **UNRUN**；11 方法、33 具名反證 |
| 原 contact-sources | **UNRUN**；15 方法、11 具名反證 |
| 原 Reading A native | **UNRUN**；7 方法、12 具名反證（11 W＋1 H） |
| 整條快路撤回 | **UNRUN**；另規劃原 7 正例的 fixed／withdrawn／restored 等價 0/0/0，不計 killed、不計完整 11 方法 suite |
| 既定 16MiB stack | **UNRUN**；新增四個 size_t[2432] 固定長度區域陣列約 77,824 bytes，實際 compiler frame 未量 |
| 效能、正式 P-189 | **UNMEASURED／UNRUN**；不新增數值門檻 |
| 完整 native、browser、全帳本、架構 | **UNRUN**；新最終來源的全帳本與架構由主代理統一處理 |
| 允許 skip／仍紅 | 原三套不允許 skip；目前未執行產品裁判，沒有本 SHA 的動態通過或已收齊紅燈聲明 |

本批僅四個檔案：W `contact_world.c`、原 C harness、原 Python contact-world suite，以及 `run_all.expected.json` 的單一 count。原 10 方法 AST、原 CHECK 與全部既有斷言／timeout 保留；舊 partial-shadow 的產品錨點移到正常快路的完整 lo/hi cover helper，另補 legacy 後備專刀。新增一方法與十刀，核實真方法數後才依共享棒登記 10→11，其餘 expected 字典逐值相同（包括 native30、faces45、noWood13）。

索引只排序面序號，不改公開輸出序。RC 前綴包含 free fixity，先進索引；member 依原 `contact_earlier()` 的嚴格先後批次插入，同 order 不互遮。lo／hi 都保原 strict-overlap 與 full-cover，直接比較完整 GeoCoord，沒有截成 32 位、座標相減或合併區間。新增正反例涵蓋過濾後的重複 ID、零長／反向跨度、完整 64 位平面與邊界值、局部平面 offset、單一見證及 survivor count。

靜態原件在 [evidence/geo300-contact-index-20261024](https://github.com/ZhiQiYang/geometry-axiom/tree/2a0772da1af26c4da9c7e104fed2a37c760668d4/evidence/geo300-contact-index-20261024)。`STATIC_ORIGINALS.tar.gz` SHA-256 為 `52e0c5329fc3a29483517995f3aad444dfb97b6553016ffb6e61eb257cdb6e26`：203 原檔＋index，共 204 成員均已回讀核 hash。內容包含完整 Git 指令／退出碼／streams、凍結草案與靜審。草案原文記錄當時 external-only 狀態，後續來源提交由 BINDING 與矩陣綁定。初次允許清單 git add 退出 1 後，只對精確的原 tracked leaf 強制加入；正常 push 均為 0，沒有 force push。reviewer 初次 quotePath checker 錯誤亦保留，首次 stderr 未獨立保全的限制已明列；沒有因此執行或重跑產品。

原三套已沿用受審 runner 準備，預計共 33 方法／56 個原具名反證，完整原 streams、每刀正常 ASSERT 的 0/1/0、0 skip、原子時限與 16MiB 均須真實通過。C 編譯目前因共用環境磁碟與主線完整帳本排程待槽，未執行；成本與性能須另等獨占窗口。#341 在 Sc493 的 32 方法／46 反證／282 builds 屬原 SHA，沒有移標為本 PR 的通過證據。

目前最不確定的是新控制的實際首個 ASSERT、額外索引在既定 stack 下的實際 frame，以及正常路徑查詢改善能抵消多少仍存的排序與呼叫成本。整條快路撤回預期語意等價，不能為取得紅燈而放寬斷言或把控制 meta-test 旁路誤記為產品缺陷。N128/256/512 的提議數值、容量512與 cut-list representation 留作後續待決，本批不採用新門檻、不改公理或決策佇列。尚未建議合併。
