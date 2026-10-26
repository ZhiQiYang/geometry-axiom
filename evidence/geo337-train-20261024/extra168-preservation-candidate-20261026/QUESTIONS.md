# 待決：固定新增 168 葉的清理範圍

這份文件不構成批准，也沒有執行新增刪除。原已批准 3156 檔與 108 空目錄的清理已完成；本範圍獨立。

候選為下列三個已退役 checkout 的私有 `.git/index`，以及固定 BYTE_MAP 中 165 個 GPU cache 葉：

- `/tmp/g261r3/source-final/.git/index`
- `/tmp/g261r3/work/codex-geo261-8f76f2b7/repo/.git/index`
- `/tmp/geo261-p73-resume-20261022-5z1cdxpj/source-proof/.git/index`

三個 index allocated 共 13,840,384 bytes；GPU 葉共 9,867,264 bytes；毛回收估計合計 **23,707,648 bytes**。完整清單及每葉路徑、身份、hash 見同提交的 `extra168-preservation-candidate-20261026/SNAPSHOT.tar.xz` 內 `BYTE_MAP.json`。沒有納入 33 個 cache 目錄、任何使用者修改、fixtures、Git objects/refs、F9 ELF 或原始收據。

完整備份已在雲端落盤並逐成員往返比對：tar.xz 723,012 bytes，SHA256 `f9770ca505999057c23c898d559836f74594bc66e90bf5c83479e3d76f0385f6`；遠端是否已核實以本次 publisher 真終態為準。備份前後 168 葉未變；三根 HEAD/refs/status 與原退役紀錄精確相同、staged 空。平台 PID 208/260 的部分 proc 不可讀，沒有聲稱完整檢視它們。後續若批准，仍須重新確認無使用者、無鎖、無內容變更；任何有疑慮者跳過保留。

選項一：在備份遠端全文核實且重新檢查均成立後，只批准刪除這 168 葉。建議此範圍；它是目前找到的具體 native 容量候選。恢復可以重建 bytes、權限與 mtime，但 inode/ctime 無法還原，故舊 checkout 必須保持退役，不能假定刪後仍可直接使用。

選項二：保留這些檔案，提供額外容量或另一個經確認且授權的可回收範圍。沒有自行更改掛載、配額、規劃守門或付費資源。

容量限制：新的來源觀測原件占用已納入。19:27:33 UTC `/tmp` 可用 111,865,856 bytes；若毛回收全數成立，扣約 507,904-byte 來源轉移永久增量後，只比原 native 128 MiB 准入多約 847,872 bytes，尚未計少量後續 metadata 與可能的 index extension。這是條件估計，不是實測已通過；也不足以解除 browser/card 的容量依賴。原 4 MiB 額外規劃餘裕已不成立，但不是降低任何原正式門檻。

在此待決期間繼續 §7 資源診斷與來源轉移準備；不等同新清理可執行。
