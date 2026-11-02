固定 R=a22df116c7e9f6b7d074451f1c8052d59e7e4f3e 的一次 N64 儀表診斷已正常退出 0。這是觀測用途，不能當新的正式效能樣本或改寫 N64/main=1.3369644933292553 的原紅燈。真正原始檔位於 `/tmp/geo323-node-hint-R-diagnostic-r3-20261024/execution/`；stdout 與原 R profile 逐 byte 相同，stderr 除一行診斷 JSON 外完全相同，原 R readonly checkout 保持 clean。

此次使用原受審儀表的 22 個精確替換；R 的 source.c 等同原 U 的受審 before.c，完整撤回也逐 byte 相同。只在私有 185 檔 quoted closure 加上儀表 include 與 entry，共 187 檔、2,147,468 bytes。實際 gcc 使用原 `-std=c11 -O1 -fno-inline -pg`、stack 16 MiB；沒有變更產品策略、分支、原裁判門檻或時限。

實測總量：node_call 2,364,478；hint hit 626,713、empty 4,080、conflict 1,733,685、invalid 0。10 個 provider/key-size 家族，family/counter overflow 均 0。indexed find 1,737,693、linear 72，find existing 1,499,086、missing/new 238,679。node hash 2,300,604；index_insert 562,911，含 rehash_insert 324,884；652 次 rebuild 全成功，fallback 0。這三個入口總數與此次 R 的原 gprof 相符，不是拿舊 U 的假設充數。

最需要處理的是既存節點的重複查找：

| 家族 | node calls | hint conflicts | existing find | new nodes | 使用的 hint 槽 |
| --- | ---: | ---: | ---: | ---: | ---: |
| WOOD_DEFINITION 19 / 5 bytes | 1,077,210 | 803,409 | 796,908 | 8,700 | 68 |
| MEMBER_POSE 2 / 4 bytes | 760,764 | 624,509 | 622,758 | 2,157 | 64 |
| CONTACT 16 / 17 bytes | 440,110 | 250,088 | 24,620 | 226,526 | 116 |
| PLACEMENT 13 / 5 bytes | 81,312 | 53,764 | 53,764 | 216 | 3 |

前兩家族占 82.36% 的 hint conflicts，槽集合交集 63、聯集 69。這是實際槽分布；儀表未記錄 victim→incoming 配對，不能宣稱所有衝突都由另一家族逐出。5-byte definition 最後 byte 為零的次數是 0；4-byte pose 全部 last_zero。不能再泛稱「長 key 末 byte 0」是唯一病因。

完整 node index 的 occupied probes 為 1,777,944，與 1,737,693 次 indexed find 比約 1.023。這包含命中及未命中；不是每次 miss 的平均探測長度，也不支持先假設完整索引有嚴重長鏈。CONTACT 占 94.91% 新節點，且單一 hint slot 0 收到 239,148 次 calls；其 query identity 是否必須保留由原來源契約決定，不能以本診斷擅自合併 query。

下一步已決定保持 K 產品策略不動，先由 W 工作線修原 plane/query 熱點並正式重測，以免同時兩刀混淆因果。尤其不能把 full hash 無條件提前到全部 hint：現有 626,713 次命中可免 hash，必須先計算新增雜湊與比較成本，不能只看命中率。只做 new-node probe reuse 最多涉及約 238k 次首次插入，本資料也不保證可消除原 1.3 門檻紅燈。後續可另備 shadow 統計，比較同 256 個位置下的 2-way、保守 cheap mixing 與完整 byte equality 的命中及額外比較數；僅觀測，不改真實查找路徑、node/edge 順序或公理語意。任何真正產品修正仍需完整撤回反證、原 ordered graph/guards、memory/fallback/collision/rehash、sealed/started 時序與正式效能驗收。

準備過程兩個非產品失敗完整保留：R1 在 workspace 32 MiB 操作空間 guard 停，0 Git/0 C；R2 在 compile 前誤要求 regex relative includes 全數可直接解析而停。R3 窄修工具分類：30 個全部是原本已受審的 public K include guard fallback，完整 185 paths 及真正 K headers 都保留，沒有補 shim 或改編譯 flags。兩個失敗都不是 mutation kill，也沒有消耗正式時間樣本。
