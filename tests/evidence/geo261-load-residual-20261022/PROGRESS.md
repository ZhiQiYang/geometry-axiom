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
