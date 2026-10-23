# A/D+B 定向功能證據（8ab0bdb4）

測試基底為 `e9c1509cf89e6f35d298743ec5e3368370316cf7`，產品來源為 `8ab0bdb467ba6e6d22f7c5652f221cffab4934b6`，分支 `codex/geo261-fix-perf-owned-replay-20261018`。本稿只記新來源；舊 `ea9→ff46` B-only 證據另行保留，沒有拿來填入新來源的結果。

兩次候選完整正控制各 **153/153**。前輪 unittest 54.155 秒／外層 54.396872 秒，恢復輪 46.628 秒／外層 46.844020 秒。八模組各為 18、17、17、7、20、53、11、10 項；這是相同 153 項的兩次執行，不宣稱 306 項不同測試。前輪後段與 formal archive build 並行；所有這些時間只作功能執行記錄，不用於正式效能比例。

B 的十個 FILE_REPLAY_JSON 案例全 exit 0，保留 I8a／D6c 診斷，沒有 B assertion failure。完整 stdout 另有 D_CONTROL_JSON 的預期負控 ASSERT，不可誤寫為「整份 stdout 沒有 ASSERT」。恢復輪是全部語義控制的共同正控制，不聲稱每個控制後都立即各跑一輪。

## 成本三段與語義負控

| 階段 | 來源 | 結果與界線 |
|---|---|---|
| 初次 before-cost | b05374d2 | 錯誤 method name，loader synthetic error；產品方法未執行，不能當紅燈。原件保留。 |
| 正確 before-cost | b05374d2 | 1 run／1 failure，6.157 秒；真 native 精確 `file-replay-inner-candidate-cost`。 |
| 修後候選完整正控制 | 8ab0bdb4 | 153/153，包括 B 成本方法。 |
| 單撤 opt-in | 341611df | 1 run／1 failure，29.786 秒；只把公開載入呼叫改回原 parser，真 native 在同一成本 ASSERT 轉紅。 |
| 恢復候選完整正控制 | 8ab0bdb4 | 153/153，包括成本、rollback 與所有語義控制對應正控制。 |

03 單撤 rollback memcpy：原 D6c 診斷之後，先 `file-replay-failed-line-byte-rollback`，再外層 `file-replay-frame-verdict`；真檔案 parser 入口避免互動 history 掩蓋。04 先 `file-replay-operation-bytes-restored`，證 operation bytes／padding 還原。05 先 `file-replay-line-graph-released`，證逐行 graph cleanup；mutant 在首個 prefix 即停，沒有宣稱其後 preview fallback 已走完。

06 先 `file-replay-describe-rejection`，07 先 `file-replay-active-source-rejected`。兩者只證 helper body 守門，不冒稱撤掉 production callsite 已被測出。外層 source-verdict／frame-verdict 是後續結果，不重複算獨立 kill。

02 為一個方法、兩個 subTest failures。valid 先命中 `file-replay-i8a-refused`，為有效 I8a 拒絕語義 kill；invalid 仍有 D1／D6b 拒絕，先命中 `file-replay-i8a-keeps-inner-owner` 計數檢查，後續原錯誤／prefix／live／preview／scope 斷言未跑。沒有把 invalid 說成被接受，也不推造未觀察的 enum 或 serial 值。原件及逐 fixture 裁決另存。

## 原始協定與個別產品案例

四態為 baseline e9、support b053、withdrawn 3416、enabled 8ab。每態六個相同案例；三個非基底狀態各 18 組 stdout／stderr／stdin 對基底，正式 **54 組逐 byte 全等**。每態 52 筆完整 command／response、12 份 fixture 與寫入順序一致。沒有正規化路徑、token、空白或行尾。此為既有 NativeBuild `-O0` 語義證據，不能拿捕捉時間宣稱效能提升。

另外，各自從 e9 與 8ab 真執行六個 product client 案例，**12 對 stdout／stderr 全等**：

| 案例 | stderr bytes | 個別原診斷 |
|---|---:|---|
| lifecycle | 372 | 正常 I8a valid preview |
| wood-tamper | 456 | preview stale 拒絕 |
| host-tamper | 456 | preview stale 拒絕 |
| before-tamper | 456 | preview stale 拒絕 |
| revision | 456 | preview stale 拒絕 |
| cancel | 442 | missing/invalid preview token 拒絕 |

六個 stdout 都空，每案各 exit 0；非空 stderr 是應保留的產品診斷。舊 e9 單一 372-byte lifecycle 收據仍保留，沒有代替其餘五個案例。372-byte原literal斷言完整保留；本次新增e9／8ab六案真baseline差分作證據，未刪除或弱化斷言，也不宣稱解除原單元測試對診斷措辭的維護耦合。這些證據涵蓋真 native confirm 與不發布見證，不能單獨證明 JSON dispatcher、K enum 或 B 快路徑；這些由各自測試、四態 raw 與單點控制分別驗證。

## 凍結與未驗界線

正式計時結束後已完成全部23個stage的身份重核；每stage原receipt列出的29個evidence檔bytes/hash皆符，來源／HEAD／工作樹穩定、無timeout/interruption/launch error。包括新增恢復輪與兩套六案例的完整原件，另有獨立審查。原fixtures與streams都保留；公開副本只把.scene改資料別名.scene.txt、stdout.bin/stderr.bin改.raw，逐bytes相同且原path/hash映射見data-copy-map.json。未改動原測試證據。

兩個暫存product client已清除，binary hash是capture當時前後驗證的原記錄，不冒稱現在重新hash得到；四個持久raw bridge則已重新核對。原outer artifacts=[]的raw/capture另行納入清單，沒有改寫收據來假稱當時已封存全部檔。

環境：Debian GNU/Linux13.6、Linux6.18.55 x86_64、gcc14.2.0、Python3.12.14、Node24.19.0、Google Chrome155.0.8059.84；child stack16MiB。版本原文隨stage保留。直接unittest通過不表示run_all expected/census已更新或strict全量已通過；最後合流仍須按計畫真正跑update-expected後再strict全量。

性能另由整合報告列真normal/gprof前20與同輪正式bridge24/24比較。root已回報main36.493秒、8ab86.818秒，約2.379倍，仍未達≤2倍門檻；首次archive bridge因缺sidecar的149skip試跑不得作功能通過或性能樣本。完整整合的非瀏覽器、瀏覽器、mutation與架構驗收不由本定向功能報告代替。

## A/D 審查後補強（同8ab來源）

K的pending摘要從迴圈寫成保存原件與目前bytes兩個明確SHA呼叫；完整memcmp與fallback語義不變。共用instrumentation精確callsite釘選隨真呼叫點從4改5，原runtime呼叫數與斷言保持；hash-actual-twice負控移到新的精確保存原件呼叫，沒有刪除負控。

H測試在before/after篡改、拒絕發布與復原路徑補精確K provider計數，並以延遲建構子重跑原H client；這些是測試補強，沒有新增產品provider守門；另將原H client的七個constructor呼叫（含六個非法參數案例）只在隔離測試副本換成opt-in，沿用十二個原case與全部斷言，新增一個method。A/D舊報告只勘誤D移除的完整重複check範圍、同輪倍率口徑與README精確hash，原875報告與測試／性能原件均保留；不因文字勘誤增加任何通過項目。
