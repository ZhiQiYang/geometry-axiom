# #348 最後產品組合對抗靜審

基底 B：`9a8584f57be7935604c3bad4c2481945a6ec3d9f`。固定受審來源 M：`7a0e6dd81c54066995981393925fa46a815de2f8`。

**在以下八檔的組合差異與直接呼叫路徑中，未發現新的合併阻斷缺陷。這是靜態審查，不是獨立執行 H7、完整 native、帳本或瀏覽器的證據，也不據此宣告 PR 可合併。**

本代理只讀 `git diff B M -- <八檔>`、固定 M blobs、當前八檔及必要直接 caller/header。八份工作檔逐 bytes 等於 M；完整差異與 Git 原 stderr 分別保存在 `eight-products.diff`、`git.stderr`，逐檔身分在 `SOURCE_BINDING.json`。沒有修改 checkout、編譯、執行測試、提交或對外發布。既有歷史 alternate 缺目錄警告仍保留；本輪所需差異及八份 M blob 讀取均 exit 0，沒有修理 Git store。

## 核對重點

1. **generic hint 並未變成值快取或省邊證明。** `geometry-core/kernel/source.c:274–300,403–414` 對 hint 先查非零／範圍，再以 provider、key_size、全部 key bytes 比對；未命中回原 node 路徑，成功才寫回 ordinal。`NULL` 原樣走 `geo_eval_depend`。sealed、非法 key、dependency kind 及原 edge 必要配置守門保留。reset 後同 ordinal 改指別 key 不會命中；同完整 key 可重用 ordinal 也仍記錄當前 consumer 的原 kind。

2. **ordered graph 仍由追加陣列決定。** `source.c:302–348` 的 fast path 僅辨認已存在的同 consumer/source/kind；新 edge 在必要 grow 成功後才追加，之後才發布最大 consumer/kind 提示。一般回查在較早 consumer 需要時先補完整 edge index。32-bit optional index 超出表示範圍或配置失敗時丟棄索引、保留 size_t 公開陣列並改線性查找（166–204），沒有 cast 後繼續使用截斷 ordinal。

3. **scope 的完整性及巢狀恢復可對上控制流。** `source.c:55–100,311–339,439–447` 僅在 consumer 尚未有 outgoing edge 時建立 complete scope。來源節點的借用 mark 原值逐筆存 undo，child 結束依反向順序還原。undo optional 配置失敗會將 scope 標不完整，保留已追加的真 edge；之後走完整索引。provider false、無效結果及一般返回都先執行 scope_end，重試失敗的既有 outgoing 不會被當成空集合。reset 清所有 node／hint／scope／dirty index（230–243），active/sealed 時 reset 原拒絕仍在（467–470）。未看到跨候選遺留的有效指標。

4. **H 三個 ordinal 欄位沿完整身份與原接線。** `reference_sources.inc:489–536,651–679,889–910` 的 definition／placement／pose 快取仍檢查 member 身分與原成功旗標，命中仍依原 consumer 和 relation 呼叫 dependency API。pose 與 footprint 共用 hint 是同 provider、同 member id 的 source identity；只共用 ordinal，不把兩者的值旗標合併。`references.inc:156–173,692–702` 在 dispose／新候選時清 member_reads 並 reset／重建求值狀態。沒有把失敗值寫成成功快取。

5. **validation memo 的生命週期與 host 借用保持局部。** `world_validation.inc:35–50,70–82,137–146` 的 anchor memo 每次 context 建立清 valid，只保存成功結果；超出容量的 index 仍交原 accessor 拒絕。host/boundary 指標借用限同一次同步 callback；所查 place／stops／end_faces／boundary caller 沒有在使用借用指標前重入同一個 AppValidationInputs。`world_validation.c:33–34` 的放置 probe 是 member 複本，不把 validation 中的 World 改寫。外層與 reference_check_all 各自建立自己的 memo，沒有候選失敗、Undo/Redo 之間的靜態快取。

6. **略過的 raw footprint 工作沒有變成失敗旁路。** `current_geometry.c:5788–5806,5891–5901` 保留原 live prefix 初始化及 raw fallback；已由 source 處理但失敗時返回失敗／0，不進 raw fallback。`reference_sources.inc:805–820` 同時保留 source_failure 記錄與後續拒絕。domain-only 只預備 W span-extension 守門所需的 placement/region/role boundary；`contact_world.c:434–442` 確認原守門在 resolver 之前，resolver 後才讀 member facts。`placement_effective_boundary` 在需要本地 storage 時自行完整清零（current_geometry.c:418–429），未因縮小 AppContactFacts memset 而留下被讀取的未初始化有效區域。

7. **W 結果 memo 必要 callback 與輸出所有權保留。** `contact_sources.c:101–166` 先執行原必要 allocations、facts callback 和 facts validation，才比較 request placement/direction/exclude、capacity、完整 facts bytes、借用 member 的 id/placed。命中後仍給新 query 分配並複製自己的 collection bytes；舊 query bytes 的生命週期至 owner destroy。optional memo allocation 失敗只停用提示；必要 collection allocation 失敗仍原失敗。FEATURE 的 collection ordinal 要先通過完整 identity、VALID 和 value 檢查，再記原依賴，否則走原 `geo_eval_source`。

8. **排序／plane index 的變動沒有改容量或幾何接受規則。** member fast path 僅用於原 unique-ID 路徑，且完整 declaration facts 的 order 已非遞減；過濾後保留穩定 subsequence 與雙側順序。非單調時先取每 face 的完整 uint64 order，再以原 `<=` stable merge 比較。plane begin/end 按原 fixed 比較器的等價區間建在同一不可變 face array/rank，查詢仍指向該陣列的原元素。沒有增加收集上限、忽略 overflow 或將超量誤判成功。B 已含512容量；這八檔屬其後效能修復，不能把它們的靜審誤當整份容量變更的獨立實跑。原 W `world_validation.c:9–10` 的超量 CAPACITY 拒絕仍存在。

## 保留界線

- 沒有執行任何編譯、mutation、H7、profiler、native、browser、allocation fault injection 或 sanitizer；不重新核收已公布 raw archives，也不改寫它們的 execution SHA。
- 對必要/optional allocation、深遞迴及低記憶體的上述結論來自控制流；正式反證與最大容量真實結果仍須沿 root 的原件及後續正式 gate 判定。
- 任意 provider 在 callback 內破壞 context／跨執行緒改 World 的行為不在現有單候選同步 API 契約內；本輪沒有為它擴充語意，也沒有據此增加新豁免。
- 本輪未宣告完整上游鏈驗收、帳本重產、架構重產、census 或 PR READY。最終採入依 root 其餘正式 gates 的真終態。

W 兩檔另由子代理獨立靜審，結論同為未見新增阻擋；詳 `wood-review.md`，不冒稱獨立實跑。該代理如實記錄一次必要 caller 搜尋誤命中巢狀 evidence 行，沒有開啟或採用其內容，後續限精確來源檔。
