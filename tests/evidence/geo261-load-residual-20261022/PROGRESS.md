# #323 修正進度（2026-10-22）

本次接續 `codex/geo261-load-residual-20261020` 的公開來源 `f3ea9c5232c043b3dca57b953577f5d22e9030e7`。這是增量修正進度，尚非 #323 最終整份驗收；不進 #288 最終來源。

| 完成項目 | 實際結果 | 原始封存 |
|---|---|---|
| sealed 內部 H footprint 相容性 | 產品只加 `!geo_eval_is_sealed` 命中守衛；真實 provider 自然 warm→seal 後同 facts 可讀，未知 pose 仍拒絕，World／provider／完整有序圖不變；撤 guard 原 0／1／0，紅為 `ASSERT:sealed-contact-facts-remain-readable` | `raw/sealed-new-01.raw.tar.gz` |
| host facts 完整 suite | 原 17 方法保留，新增 3 方法；20 tests，原退出 0、無 skip；15 負例皆原具名 ASSERT | `raw/sealed-full-02.raw.tar.gz` |
| W collection 跨 feature 依賴 | 原 12 方法與六控制全保留，新增兩方法；14 tests，原退出 0；第二 feature 省邊／改 kind／反向求值次序三控制各原 0／1／0，紅為 `ASSERT:collection-cache-second-feature-edge-and-order`；完整九邊以公開 source key、kind、次序核對 | `raw/collection-full-01.raw.tar.gz` |

以上診斷在 `f3ea9c52` 的明列工作樹 patch 上執行，收據保存完整前後 patch、命令、真退出、環境、stack、subreaper 與 stdout／stderr。測試新增的可選 execution JSONL 保留每次原生文字 stdout／stderr；不是二進位輸出的宣稱。各 NativeBuild 編譯原 log 與暫存 C/header/include 輸入於刪除暫存之前封存，未收 ELF／object。

公開端面仍遵守 W 的 sealed 新 query 拒絕政策；本次不宣稱公開端面流程在 sealed 變成可用。產品層守衛不改 K/W sealed 語意，不改公理、決策佇列或守門流量。

下一步：補實際 member_reads 鍵／失效與 H 跨 consumer kind／有序圖負控制，完整跑 19 個 PF3 mutants；最後固定新來源，依影響更新帳本／架構並執行完整 native、175 場景 A/B/C、36 次交錯量測及 profile。此處沒有將歷史完整紅燈外推成新結果，也尚未宣稱 #323 完成。

## member_reads 與 H consumer 控制完成

`load-residual-full-01` 真退出0，12 tests／48.043秒／無skip，原7方法全保留，新增5方法。58次原生文字execution均留完整argv／rc／stdout／stderr／環境／exe SHA：42次rc0、16次具名rc1；每個新增負控制皆baseline0／mutant1／restored0，另有如實保留的placement單刪等價。

| 新控制 | 原具名失敗 |
|---|---|
| definition第二consumer省邊／改kind | `ASSERT:definition-cache-second-consumer-edge-and-order` |
| anchor第二consumer省邊／改kind | `ASSERT:anchor-cache-second-consumer-edge-and-order` |
| footprint第二consumer省邊／改kind／提早讀definition改次序 | `ASSERT:footprint-cache-second-consumer-edge-and-order` |
| pose第二consumer省邊 | `ASSERT:pose-cache-second-consumer-edge-and-order` |
| pose命中將requested kind改錯 | `ASSERT:pose-cache-preserves-requested-dependency-kind` |
| 同storage slot不同canonical member id | `ASSERT:member-anchor-cache-id-must-match` |
| anchor miss不清除自然warm的footprint | `ASSERT:member-anchor-miss-invalidates-footprint` |
| 明列anchor-invalidator fault前置下再撤placement guard | `ASSERT:contact-footprint-cache-placement-must-match` |

H oracle比較每一consumer完整有序source key／kind序列、原prefix有序圖、節點插入序、重讀去重、World不變及sealed既有值讀取；突變只對第二個真consumer啟用，不由第一個失敗遮蔽。member fixture透過真實註冊H/W/K provider自然warm，以成對storage permutation保持每id的canonical定義、pose及場景語意，不寫入偽造memo值。

**placement單刪不是killed。** 本候選的canonical anchor host在同id下固定；換id先由anchor miss使footprint失效。單獨刪除placement比較原0／0／0，保留為此合法生命期夾具的等價結果。配對防線以明列的「anchor invalidator已撤」作固定前置，證明placement guard在跨兩真host仍是第二防線：0／1／0；它不構成單fault必要性的證明，不改K/W生命期湊紅。

`h-cache-positive-01` 為新增fixture缺陷，原退出1（五個setup FAIL）：provider註冊錯放在第一次求值之後，違反既有K註冊鎖定規則。修正只把測試provider註冊移到warm前，原斷言與產品不改；`h-cache-positive-02` 原退出0。兩份原輸出均保存，不把setup紅算mutation kill。

member獨立probe的01保留輸入綁定缺口：當時untracked新include未在Git patch中；02-bound-inputs將五個原輸入及compiler實讀snapshot逐bytes/hash固定，原12次結果與01一致，工具／判準未改。整合load-residual suite另將新include複製進NativeBuild工作目錄，compiler實際輸入亦完整封存。

下一步在新公開產品／tests提交上實跑完整19案PF3工具、前三已修suite與原必要八suite；之後由整份帳本／Linux架構與固定最終SHA原完整native、175 A/B/C、36交錯量測及profile收尾。本段仍為進度，不宣稱#323完整驗收完成。
