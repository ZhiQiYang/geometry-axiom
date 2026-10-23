這份 GEO-300 前置候選把擋面逐次刪除的尾端搬移，改成依原順序停用、最後一次穩定壓緊。保留原收集、容量截斷、穩定排序及完整遮蓋判斷；超過既有 face capacity 的公開 caller buffer 仍使用原 memmove 後備。它尚未通過本分支的動態驗收，也沒有量測出的效能改善。

唯一 current-state 矩陣：

| 項目 | 實際來源／證據 | 結果與範圍 |
|---|---|---|
| 基底 | a048530c18f5df43a921e6b06bb3e4aa2192684e | 已公開 train；排除根 evidence 後與 F4f 產品／測試 diff 為空 |
| 產品 SHA | 576d3e1b3589bdea303aae481e66a4b8b25d818b | 三個 leaf：contact_world.c、原數值 harness、原 W 接觸 Python 套件；不是本候選驗收已綠 |
| Evidence head | ea3187ac30855253945094741da40507abb69b60 | 普通 push、ls-remote 同；evidence/geo300-prerequisites-20261024/ |
| 權威讀取 | main 425c092eaf16f90256d76433243baebde45163ac；handoff e91e8e0c82afd9ae784e25fe63566f3e42f4b2d4 | fresh fetch exit 0；決策指定日期、公理、FIELD-RULES、舊草稿完整原件與 hash 封存；handoff/pr-reviews/300.md 不存在，原 Git exit 128 保留 |
| 候選靜核 | frozen v1：108 項 | 1 個基底既存失敗：原 free-end control anchor 已有三處；不冒稱整體靜核全綠，單行維護 leaf 另由主代理處理 |
| 獨立對抗靜審 | train_adversarial_review，57 checks／0 新 findings | 限 active-set 等價、後備與控制設計；原 free-end 失敗、動態與效能未驗限制均保留 |
| 候選原 W 接觸套件 | S576d3e1b，10 methods／23 controls | UNRUN；原 9 methods／18 controls 全保，新增一個具名方法及五個 control |
| 新反證 | inactive-shadow、compact-active-only、compact-survivor-count、dedup-strict-overlap、dedup-full-coordinate | 真正編譯與原 ASSERT 0/1/0 全 UNRUN；編譯錯、crash、timeout 不算被偵測 |
| 操作／效能 | S576d3e1b | UNMEASURED；沒有新時間、記憶體或操作次數門檻，沒有幾倍加速聲稱 |
| 原生、瀏覽器及其餘專項 | 本候選 | UNRUN；F4f 或歷史分支結果沒有移作本候選驗收 |
| 架構、全帳本與 shared registry | 本候選 | 尚未重產；主代理合流維護 expected count 9→10，tests/mutate.py／全帳本由主代理統籌 |
| 本分支允許 skip | 無已跑 subject | 沒有跳過後記綠的項目；目前正式 subject 全部 UNRUN |

公開封包都逐檔從 tar 讀回完整 bytes/hash。權威封包 SHA-256 為 `09ac378a7b9944c2aa2b09170c6870083075811ec9300d4d2dd210b156fc5a81`；候選靜態原件與 peer 封包為 `3f6913641119c4eb074f6814564a454a015b050b6b7441c6237f50273cf69768`。首輪 git add 因 sparse checkout 的忽略祖先回 1，原命令與流保留；隨後只對精確三個已追蹤 leaf 使用 git add -f，沒有 force push。

新數值見證涵蓋重複 ID 的 min/last 循環（最後一對面必須存活）、容量截斷後不得補收後續成員、零／反向區間的 strict overlap、完整 64 位不同平面、caller tail 與超標準公開 buffer 的原後備。全部優化撤回應仍語意等價，故不把原算法語意仍綠冒成突變被殺；成本差異須另用真操作或效能證據驗證。

ContactOrderIndex 與 K node/edge 索引已存在，本次不重做。配對掃描與 insertion sort 最壞平方項、呼叫次數膨脹、cut-list 平方儲存都還在。UNIQUE_ID_FOLLOWUP.md 只記未實作的後續區間索引構想，不是已完成 O(F log F) collector。

本分支不改公理、決策佇列、Reading A、RC 剩餘裸露連續段規則、容量或 16 MiB stack 契約。QUESTIONS.md 不採舊草稿 2 MiB／30 秒新門檻。合流前須完成本候選原裁判、反證、影響收據與全帳本，仍不建議合併這份未驗候選。
