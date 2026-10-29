# #348 全帳本回收對抗核收

核收時間：2026-10-29 16:21:39 UTC。固定原執行 SHA：`7a0e6dd81c54066995981393925fa46a815de2f8`。

結論：未發現這份本地回收包的採入阻擋。只核既有原件、複本、腳本與 manifest，沒有重跑原回收 helper、`mutate.py`、測試或編譯；沒有重讀 175 支 ELF 的 182,733,328 bytes。不能把本件視為新測試輪次或完整產品驗收。

## 實際核對

- 靜讀 `recover.py`、`verify_execution_links.py`、`RESULT.json`、`ORIGINAL_MANIFEST.json` 與 `EXECUTION_LINKS.json`。兩個 helper 只讀原 source/cache 並寫自己的 recovery 目錄，未呼叫產品、compiler 或 Git writer。
- **697 個唯一 member 全數讀取驗證**，每個複本及其原件的 bytes、regular-file mode、mtime_ns、SHA256 均與 manifest 一致，零失配／symlink。合 **14,330,005 bytes**。
- 原 17 個 top-level command 的 **34 個 stdout/stderr 引用**，全部與已保存 receipt 中的 bytes/hash 相符。
- bridge build＋test 的 **636 個 stream 引用（428 個唯一 raw 檔）**全部對上 copied-manifest SHA256；baseline 重複引用沒有假算成獨立檔。
- 原 ledger 有 123 個 ID；120 個非 retired 的 `execution.head` 都是完整 M；3 個 retired 沒有冒稱執行。分類與先前規則核對一致：**114 killed／1 crashed／5 equivalent／3 retired**。
- 原 receipt 的 precheck 1、完整 full-ledger 0、checkafter 0 皆保留。原 precheck 紅燈沒有被新的終態覆寫；source_before/source_after 在該 receipt 都是 M、空 status。
- recovery 目錄當下所有檔案邏輯合 **14,965,781 bytes**、實際 blocks 合 **16,252,928 bytes**，均小於限定 **31,457,280 bytes（30 MiB）**。本 PEER 文字另增不足 4 KiB，不影響結論。

## 保留界線

1. core 每次內層 oracle 的結構化結果與 stdout/stderr SHA 在原 ledger，但原 mutator **沒有保存那些個別完整 raw stream**；`RESULT.json` 已如實列限制。完整 top-level mutate stdout/stderr 不等於每支 core 的全部內層輸出，不應在發布文字合稱全部 inner raw 齊備。
2. 175 支 ELF 仍在原 cache。此輪 recovery helper 已核 ELF 與 sidecar／execution 關係；本對抗核收只讀其 manifest／連結結果，**未獨立重算 ELF hash**，也沒有把它們複製到 30 MiB 包。不可聲稱 ELF 已包含於這697檔或已遠端保全。
3. 回收目錄本身尚不等於遠端發布。本件不證明 publish、adoption commit 的 `--check` 或後續 native/browser 通過。
4. `verify_execution_links.py` 逐一核67個core、53個bridge的120條執行鏈；bridge 本輪無重試型 crashed，M20 是core三次存取違規。因此其 baseline/mutant/restored 與 build 的636引用覆蓋此次bridge原件；不泛稱該工具適合未來所有多次重試形式。

純核收命令 exit 0；來源與原執行身分沒有改寫。規則完整說明另見 `rules-review.md`。
