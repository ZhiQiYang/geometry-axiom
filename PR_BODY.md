此變更在全部 fact ID 唯一且仍在既有容量內時，將擋面的兩兩遮蓋查詢改成每個完整座標平面的 Fenwick prefix-max 查詢。索引保存單一實際覆蓋面；兩個半面不能合成一個見證。任何 fact ID 重複（包括後來被過濾的 fact）或超容量輸入，仍走原有後備。

基底是 `codex/geo260-ac23-proof-20261024`。本 PR 接續 #341 已做的活集合與一次壓緊前置；原 member insertion sort、重複 ID 後備配對、超容量 memmove 與 cut-list 平方儲存仍在，整個 collector 的平方成本尚未解除。

| 唯一 current-state 矩陣 | SHA／結果與範圍 |
| --- | --- |
| Product SHA | `1ee4e830399b124ebd63c5ff51064d87e53f38d9`；包含產品 `9ee7f98144f81f11385f392e13cc067f1b9d063c` 與真新增方法對應的 expected 10→11 |
| Evidence head | `4f456effd0a53ec45e575c2ce3596825b8dc937a`；僅新增本 PR 的 evidence prefix，產品內容與上述 S 相同 |
| Base | 公開 GEO260 evidence `df230da57619e437c30527dbede8c67fd0ec6b50`；產品 `eb846c345881cc6fc73a53c457a291175365b88c` |
| 靜態驗證 | 凍結草案 157 checks／0 findings；核心 15 機械檢查＋8 語意觀察／0 findings；不可變 Git 來源、expected 與原 push 167／0。各自 scope 限於靜態／Git 證據 |
| 原 wood-contact-world | **exit 0**；11 方法／33 具名反證正常 0/1/0；0 skip；131 builds 全 0 |
| 原 contact-sources | **exit 0**；15 方法／11 具名反證正常 0/1/0；0 skip；85 builds 全 0 |
| 原 Reading A native | **exit 0**；7 方法／12 具名反證（11 W＋1 H）正常 0/1/0；0 skip；86 builds 全 0 |
| 原件獨立審查 | 1140 checks／0 findings；共 33 方法／56 反證／302 builds；原 driver／reaper／launcher／host tool 皆 0，HEAD／tree／clean 全保 |
| 整條快路撤回 | **UNRUN**；另規劃原 7 正例的 fixed／withdrawn／restored 等價 0/0/0，不計 killed、不計完整 11 方法 suite |
| 既定 16MiB stack | 上述原三套在 16MiB limit 下全 0；四個 size_t[2432] 固定長度區域陣列資料約 77,824 bytes，實際 compiler frame 與完整場景上限仍未另量 |
| 效能、正式 P-189 | **UNMEASURED／UNRUN**；不新增數值門檻 |
| 容量512、容量收斂、cut-list 平方儲存 | **未完成／未驗** |
| 完整 native、browser、全帳本、架構 | **UNRUN**；新最終來源的全帳本與架構由主代理統一處理 |
| 允許 skip／仍紅 | 原三套皆 0 skip、沒有本輪三套紅燈；其餘未跑項維持未跑，不計通過；尚未 READY |

本批僅四個檔案：W `contact_world.c`、原 C harness、原 Python contact-world suite，以及 `run_all.expected.json` 的單一 count。原 10 方法 AST、原 CHECK 與全部既有斷言／timeout 保留；舊 partial-shadow 的產品錨點移到正常快路的完整 lo/hi cover helper，另補 legacy 後備專刀。新增一方法與十刀，核實真方法數後才依共享棒登記 10→11，其餘 expected 字典逐值相同（包括 native30、faces45、noWood13）。

索引只排序面序號，不改公開輸出序。RC 前綴包含 free fixity，先進索引；member 依原 `contact_earlier()` 的嚴格先後批次插入，同 order 不互遮。lo／hi 都保原 strict-overlap 與 full-cover，直接比較完整 GeoCoord，沒有截成 32 位、座標相減或合併區間。新增正反例涵蓋過濾後的重複 ID、零長／反向跨度、完整 64 位平面與邊界值、局部平面 offset、單一見證及 survivor count。

靜態原件在 [evidence/geo300-contact-index-20261024](https://github.com/ZhiQiYang/geometry-axiom/tree/4f456effd0a53ec45e575c2ce3596825b8dc937a/evidence/geo300-contact-index-20261024)。`STATIC_ORIGINALS.tar.gz` SHA-256 為 `52e0c5329fc3a29483517995f3aad444dfb97b6553016ffb6e61eb257cdb6e26`：203 原檔＋index，共 204 成員均已回讀核 hash。內容包含完整 Git 指令／退出碼／streams、凍結草案與靜審。草案原文記錄當時 external-only 狀態，後續來源提交由 BINDING 與矩陣綁定。初次允許清單 git add 退出 1 後，只對精確的原 tracked leaf 強制加入；正常 push 均為 0，沒有 force push。reviewer 初次 quotePath checker 錯誤亦保留，首次 stderr 未獨立保全的限制已明列；沒有因此執行或重跑產品。

原三套在 2026-10-23 21:55:09.059797～21:55:31.974441 UTC 於固定 S 實際完成，共 33 方法／56 個原具名反證；每刀原正常 ASSERT 的 0/1/0、0 skip、原子時限與 16MiB 皆保持。原 logs 的 builds 為 131＋85＋86＝302，全部 0。secondary 槽位已在真終態釋放，source 沒有再修改。因可用空間，僅 out／TMPDIR／bound observer／reaper log 移到 /tmp，原 100MiB preflight 改查真正 /tmp 容量且門檻不變；另經 18／0 機械差分 peer。這段時間是執行紀錄，沒有作為效能比較。#341 在 Sc493 的 32 方法／46 反證／282 builds 屬原 SHA，沒有移標。

本輪完整實際原件為同目錄 `THREE_SUITES_ORIGINALS_AND_PEER.tar.gz`，SHA-256 `09b50ede5a8e932ef8bb6b69348a810ebbf1db7433908b02e83b751d8172f24d`：356 raw／20,889,604 bytes，加工具與 peer 共 366 成員逐件回讀；Git blob `ed411e2ea637a43cd5efae1923541395edac671c` 直接入庫而未再物化 archive。NativeBuild logs／native events 保完整解碼文字；最外 host tool exit 0 依原 API 回覆，沒有獨立 host OS capture，reaper／driver／三套原 streams 有 c387 收據。reviewer 初始 schema probe／expected_assertion 取值修正原件保留，沒有 subject 重跑。

目前最不確定的是完整場景下的 stack 上限，以及正常路徑查詢改善能抵消多少仍存的排序與呼叫成本；這三套通過不代替完整 native、browser、架構、全帳本或性能。整條快路撤回的七正例等價實證仍未跑，不能為取得紅燈而把控制 meta-test 旁路誤記為產品缺陷。N128/256/512 的提議數值未採為新門檻，容量512、容量收斂與 cut-list representation 仍未完成；不改公理或決策佇列，尚未 READY 或建議合併。
