這份 GEO-300 前置候選把擋面逐次刪除的尾端搬移，改成依原順序停用、最後一次穩定壓緊。保留原收集、容量截斷、穩定排序及完整遮蓋判斷；超過既有 face capacity 的公開 caller buffer 仍使用原 memmove 後備。候選尚未通過動態驗收，也沒有量測出的效能改善。

本 PR 的 base 是 `codex/train-337-continue-20261024`，只作未完成驗收的 draft；不改以 main 為 base，不合併 PR。

唯一 current-state 矩陣：

| 項目 | 實際來源／證據 | 結果與範圍 |
|---|---|---|
| 新列車基底 | a6072dde8eac809e93ccd9373946dea98fa5c362 | 含 Claude 的 M151 owner-map 及 root 精確 free-end 單行維護；已一般 merge，exit 0／零衝突 |
| 候選產品 SHA | c493b7315d0cd3b16014add96af969c49ebf4660 | 相對新基底只三個 leaf：contact_world.c、原數值 harness、原 W 接觸 Python 套件；兩個 C 與先前已審候選逐位元組相同 |
| Evidence head | 383c13c4eb9a2f99ed62f7222463831c95cdd00e | 普通 push、ls-remote 同；evidence/geo300-prerequisites-20261024/ |
| 新合流靜核 | frozen v2，108 項／0 | 23 個 control 錨點均唯一；保新基底的精確 free-end，原方法、ASSERT、timeout 及五個新控制都保留 |
| 獨立對抗靜審 | 原算法 57 項／0 新 findings；本次普通 merge 58 項／0 | 只核活集合等價、來源聯集及控制設計；不是動態驗收或合併許可 |
| 候選原 W 接觸套件 | Sc493b731，10 methods／23 controls | UNRUN；原 9 methods／18 controls 全保，新增一個具名方法及五個 control |
| 五個新反證 | inactive-shadow、compact-active-only、compact-survivor-count、dedup-strict-overlap、dedup-full-coordinate | 真正編譯及原 ASSERT 0/1/0 全 UNRUN；編譯錯、crash、timeout、skip 不算被偵測 |
| source／Reading A 原生專項 | 本候選 | UNRUN；接在主代理指定的 noWood、faces43、GEO260 retry 之後取得 C 時槽 |
| 操作／效能 | Sc493b731 | UNMEASURED；不與當前完整帳本同跑成本／效能量測，沒有新數值門檻或加速倍率 |
| 完整 native、6 browser 及其餘專項 | 本候選 | UNRUN；基底或歷史分支綠燈沒有轉標為本候選通過 |
| 架構、全帳本、shared registry | 本候選 | 尚未為本候選重產；expected count 9→10 由主代理依合流順序統籌，子代理未寫全帳本或 shared registry |
| 本分支允許 skip | 無已跑 subject | 沒有跳過後記綠的項目；目前正式 subject 全部 UNRUN |

新靜態封包為 `MERGED_CANDIDATE_STATIC_ORIGINALS.tar.gz`，SHA-256 `09b0bd258d3791ead169f3cfb47f350f25ae8f3d3212fc85f4bafdef08d5eab7`，每個 tar member 均從封包讀回完整 bytes/hash。新合流 peer SHA-256 為 `1f6e463b5d3e17b8937131234111ab005ddb094784cfda6e9a57c0ed678b9232`。

首版固定權威讀取來自 main `425c092eaf16f90256d76433243baebde45163ac`、handoff `e91e8e0c82afd9ae784e25fe63566f3e42f4b2d4`，原命令／退出碼／環境／完整輸出與權威 hash 保存在舊封包。當時 handoff/pr-reviews/300.md 不存在，原 Git exit 128 保留，不補造審查。合流時已重新 fetch 新 train／handoff，沒有把 handoff 分支合入產品。

歷史 v1 的 108 靜核有一個原 free-end 三命中失敗，原 raw／失敗／靜審仍保留，沒有回改成綠。新基底已包含另經反證的精確單行維護；它在 `4f4a24d76e816274bfae06868b4dbf31f0860299` 的原九方法 1/0/1/0 只證該 test-leaf，不能當作這個新候選十方法已通過。

數值見證涵蓋重複 ID 的 min/last 循環（最後一對面必須存活）、先截斷後去重不得補收後續成員、零／反向區間的 strict overlap、完整 64 位不同平面、caller tail 與超標準公開 buffer 的原後備。整個優化撤回應仍語意等價，不把原算法語意仍綠冒成突變被殺；成本差異須另用真操作或效能證據。

ContactOrderIndex 與 K node/edge 索引已存在，本次不重做。配對掃描與 insertion sort 最壞平方項、呼叫次數膨脹、cut-list 平方儲存都還在；不聲稱 O(F²) 已消失或容量 512 前置已完成。UNIQUE_ID_FOLLOWUP.md 僅為未實作的後續構想。

本分支不改公理、決策佇列、Reading A、RC 剩餘裸露連續段規則、容量或 16 MiB stack 契約。不採舊草稿 2 MiB／30 秒新門檻。正式合流前須完成本候選原裁判、反證、影響收據與最終全帳本；目前不標 READY。
