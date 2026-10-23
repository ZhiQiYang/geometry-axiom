GEO-300 前置候選把去重時反覆搬移整段 tail，改為依原順序停用、最後一次穩定壓緊。在 Sc493 的三套原 C 裁判已通過 32 個方法與 46 組具名反證；成本與效能尚未量測，完整 native、browser、架構及最終全帳本仍待完成。

本 draft 的 base 是 `codex/geo324-faces-20261024`（#339，已含 #340），由主代理依共享順序合流；維持 draft，不標 READY。

唯一 current-state 矩陣：

| 項目 | 實際來源／證據 | 結果與範圍 |
|---|---|---|
| 新列車聯集基底 | 1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599 | 已普通 merge #339/#340，exit 0／零衝突 |
| 目前產品 SHA | aa0e3938f17dc996ef5e7410db4844b31856d2a6 | parent S8615；相對基底恰三個 leaf 加 expected 單一 count 9→10 |
| Evidence head | 823729be5f4f025aebbf02c2dc85e09907c28812 | 普通 push 0、ls-remote 同；evidence/geo300-prerequisites-20261024/ |
| 本輪實際 C 執行 SHA | c493b7315d0cd3b16014add96af969c49ebf4660 | 原乾淨薄 source；20:41:37–20:41:58 UTC；secondary slot，16 MiB stack、原子時限、原完整入口均保 |
| 原 W 接觸套件 | Sc493：10 methods／23 controls | 原退出碼 0，0 skip；原九方法、十八控制及新方法／五控制全執行 |
| 原接觸來源套件 | Sc493：15 methods／11 controls | 原退出碼 0，0 skip；八原控制及三 cached-collection 控制全保 |
| 原 Reading A native | Sc493：7 methods／11W＋1H controls | 原退出碼 0，0 skip；W 與實際 H collector 原入口均執行 |
| 五個新反證 | inactive-shadow、compact-active-only、compact-survivor-count、dedup-strict-overlap、dedup-full-coordinate | 各真編譯，原具名 ASSERT 0/1/0；全 46 組普通控制也都是 0/1/0。另保留原 atomic bridge 額外事件 |
| 編譯／退出保全 | Sc493，原 111＋85＋86＝282 條 build/link | 全部 exit 0；原 subject／reaper／launcher 均 0，完整 stdout/stderr、環境、source／tree／index 已封存 |
| 獨立 actual 對抗審 | 原件 1020 checks／0 findings | 只證上述 Sc493 部分原裁判；不是完整 native、browser 或效能驗收 |
| 後續合流／登記 | S8615 普通合流，Saa0 只登記 count 9→10 | 原九方法 AST 全保、新方法共十；其餘 expected 全同，noWood13／faces45 保留。原 strict comparator 9 拒／10 收／11 拒，獨立靜審 36／0 |
| 執行後來源閉包 | Sc493→Saa0 | 全部 C/H/inc、三原套件與 native 支援碼無差；詳 SOURCE_CLOSURE_AFTER_MERGE.json。Saa0 沒有另跑 subject，原收據 SHA 仍為 Sc493 |
| 完整優化撤回、操作／效能 | 本候選 | UNRUN／UNMEASURED；完整撤回應語意等價，不冒作語意突變被殺；沒有新數值門檻或加速倍率 |
| 完整 native、6 browser 及其餘專項 | 本候選 | UNRUN；基底或歷史綠燈沒有改標為本候選完整通過 |
| 架構與完整帳本 | 本候選 | 尚未重產；完整帳本由 root 唯一統籌，子代理未產生全帳本 |
| 允許 skip | 上述已跑三套原 C 裁判 | 無；實際 0 skip，編譯錯、crash、timeout 或缺工具均不當作反證偵測 |

正式原件 350 files／19,527,338 bytes，連同原工具、所有實際編譯 C、H collector 原資料、獨立 peer、普通 merge 與 expected 原命令／streams，封入 `C493_THREE_SUITE_ORIGINALS_AND_PEER.tar.gz`，SHA-256 `145048fb4827ec6180e9798dd0beeec0facc2e4e45215c581d1b78e88df1bc0f`。456 個成員全部從 tar 讀回核 bytes/hash。actual peer SHA-256 為 `fb2784a569881f3b5b5b38641138ff23ba7b228faf2432ffc742e596e49ffb57`；expected peer 為 `627013a04fc1023ab4916f1bf832169997cd5a0b79b5c7321ada33418e18cfa1`。

我先前口述把 build 總數加成 302；原收據一直是 111／85／86，正確總數為 282。原錯誤、peer finding、追加更正均保留，沒有改原 subject 或重測挑綠。peer 首版工具對缺少 timeout_expired 欄位的事件發生 schema 錯，也保留原工具歷史，沒有補造 subject 欄位。

捕捉限制：原 NativeBuild／native event 的子程序輸出是原 decoded text，並非解碼前 OS bytes；原工具會清除臨時 ELF，留下原編譯命令／完整 text logs／實際編譯 C 與執行檔 hash。最外層 launcher 的完成 0 由 host exec session 回傳，reaper／driver 及三套件的原 streams 則有獨立 c387 檔案。

保留原收集、容量截斷、穩定排序、完整座標與完整遮蓋判斷。標準容量內只以 active bitmap 保存原動態存活集合，再穩定壓緊一次；超過既有 face capacity 的公開 caller buffer 保留原 memmove 後備。數值見證含重複 ID 的 min/last 循環、先截斷後去重不得補收、零／反向區間的 strict overlap、相差 2³² 的不同平面與 caller tail。

ContactOrderIndex 與 K node/edge 索引已存在，本次不重做。配對掃描的最壞 O(F²)、insertion sort、呼叫次數膨脹及 cut-list 平方儲存都還在；不聲稱平方項已消失或容量 512 前置已完成。UNIQUE_ID_FOLLOWUP.md 僅是未實作構想。

歷史 v1 的原 free-end 三命中失敗及當時靜審仍完整保留。root 的精確單行維護在 `4f4a24d76e816274bfae06868b4dbf31f0860299` 曾做原九方法 1/0/1/0，只證該 test-leaf；本次十方法通過另以 Sc493 原件證明，不挪用歷史結果。

本分支不改公理、決策佇列、Reading A／RC 剩餘裸露連續段規則、容量或 16 MiB stack 契約。不採舊草稿 2 MiB／30 秒門檻，未核可新數值只列 QUESTIONS。來源與 shared expected 棒已交下一個 GEO260 owner；本分支後續只封自己的 evidence／正文，正式列車與全帳本由主代理統籌。
