# GEO-300 capacity 512 progress

產品 SHA：400a6d0ca50f3aca104fb569c77c8ef753c93355；分支 `codex/geo300-capacity512-20261024`。從 #128 P2 evidence `6d9d46e8d16af75351924c6d47a078d3eb647cc0` 建立，正常 merge #346 evidence `eaf15e239324a6464a04740647afccce3a3c17c7`，merge commit `696f7f07846c6224775dab5736bd1dc45541a4bf`。沒有改其他工作線分支。

## 唯一 current-state

| 項目 | 結果／界線 |
|---|---|
| 產品七 leaf | W 唯一容量 512；H admission／真 arrays／contact／cut-list／span 共用；validation 超容量在 callback 前拒絕 |
| 測試六 leaf＋registry兩 leaf | 原 64 witnesses 保留；新增 W 七方法、H 五方法；AST 7／5，尚未 runtime discovery |
| 一般 merge／apply／diff check／一般 push | 0；公開 S 如上；current_geometry.c 原 CRLF 保留 |
| 草稿／實際套用獨立靜審 | 產品計畫 12/0、W 39/0、H＋registry 60/0、實際15 leaf 73/0 |
| W／H 新 suites、ABI compiler controls | **UNRUN** |
| 原 contact／report／panel suites | **UNRUN at this S**；不把 #346 或 P2 的舊 SHA 綠燈貼到容量512 |
| 新撤回／恢復反證 | **UNRUN**；測試已備，不當作 killed |
| 完整 native／6 browser／專項／效能 | **UNRUN** |
| 最終突變帳本／架構三裁判與四檔收據 | **UNRUN**；交主代理依最後來源統一重產 |
| 允許 skip | 無新增；目前沒有正式執行，不能宣稱 0 skip |
| 狀態 | **NOT READY**；正式 C 時槽尚未授權 |

W companion 分別驗原64、真512、真513拒絕。validation 的512正例是未放置成員，不能當作512個已放置角材的幾何／施工驗收。H companion 使用真 bridge／World，準備512宣告與513拒絕、既有ID更新、undo／redo／dump/load byte identity，仍全未跑。

安全反證界線：撤 declaration guard 只呼叫 direct API；撤 H guard 只送缺 ID 的 sentinel，在 append 前語法拒絕。不得把有效第513成員送進已撤 guard 的固定512陣列。七 ABI 負例只預期具名 typedef 編譯拒絕並恢復編譯；不把異構 mutant objects 連結後執行。

登記保留所有既有 entries 的 bytes/order/values，P2=13、report=11，僅加7／5；沒有更新 mutants_results 或 tests/mutate.py。沒有新增耗時數值門檻、改SSOT／決策／K。H v1 swallowed assertion 與 registry sorting churn 已修，v1完整保留；實際套用 peer 初 matcher 把舊 members[64] 誤寫成 enum，原稿與修正也保留，均非產品執行。

完整靜態原件包 original-capacity512-drafts-and-static-reviews.tar.gz：578 members、751021 bytes、SHA-256 0b6ea82d93952e40dc199483828c3e595401720f4e36da755022e9e8fe016542。每件原 path/bytes/hash 見 RAW_INDEX.json；可解析 S 的15個公開 Git blobs與指令/退出碼皆保存。

下一步：主代理授槽後，在固定公開 S 跑原裁判與新 W/H suite；依真紅原因修復並補撤回／恢復，最後由主代理統一帳本與架構。順序 #343 → #346 → #128 P2 → 本線。NOT READY。
