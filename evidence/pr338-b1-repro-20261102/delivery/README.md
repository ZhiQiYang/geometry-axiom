# B1 正式原件的長期固存

實際 CI／工具 execution 是 `c7feff8036ed000d6dc9c7afc44c6509075de097` 的 [run 41337519632](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41337519632)，產品實際執行來源是乾淨 F8 `75a1e93811a52b69385cbdaf6a09d773ed9052ad`。目前 #338 產品 head `9230a3dc04233e50c0bf97141a7fbe692828b2ca` 另有 [run 41333092348 七項全綠](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41333092348)。本目錄僅靜態固存已執行原件，不能把 execution 改標成此資料提交。

三個精確原 SHA／bytes／完整 mode `0100700` 先在 [reproduction job 124940370217](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41337519632/job/124940370217) 核符，再由原、逐 byte 未改的 whole-memo driver 在 [formal job 124940790645](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41337519632/job/124940790645) 實跑：

| 原裁判項目 | 真退出碼與結果 |
|---|---|
| 原 R8 fixed profile baseline | 既有 exit 0；calls `82668 → 364369`，N64/N32=`4.407618425509266 ≤ 4.5`，原有效樣本不重抽 |
| withdrawn-two-C profile | 新實跑 exit 1；calls `175858 → 1064615`，ratio=`6.053833206336931 > 4.5`，具名原 criterion 紅 |
| restored profile | 新實跑 exit 0；calls `82668 → 364369`，ratio=`4.407618425509266 ≤ 4.5` |
| isolated 175／350 ABC | 新實跑 exit 0；175 scenes、350 observations、700 plain／trace 原呼叫，完整 stdout／stderr／有序 graph／五 guards 四元組全等 |
| 原 whole-memo driver／外層 | 真 process exit `0／0`、passed=true、errors=[]；F8 source before／after 均 clean |

**原 R8 overall exit 1 保留**。本次新 profile 屬既定撤回／恢復反證，沒有覆寫或重標原 R8 36 timing 樣本／四 profile 原件，也沒有以 isolated ABC 回填原跨版本紅燈。185 個編譯輸入與 171 個固定場景的 F8／9230 Git bytes 全等；另 4 個 generated 場景保留原 bytes／hash pin，沒有重產，共 175 個場景輸入核符。六份原工具硬 pin 與原 V3 封存來源都可追。B1 最後解除仍由 ChatGPT／dot 審查方判斷，這裡的 `b1Closed=false` 不自行改成 true。

## 檔案

- `EXACT_R8_ELFS.tar.gz`：三個已核符原 SHA 的可下載 ELF bodies；gzip 內為 CI 原 input tar，沒有改其 tar headers 或 ELF bytes。完整 mode 可從 regular-file type 與 `0700` 合為 `0100700`。
- `FORMAL_RAW.tar.gz`：成功 CI ZIP 內 **全部 5,405 個 `formal/` 檔案**，解壓檔案 bytes 共 48,678,394。含三 phase 原 receipts、private ELF／變體 source、全部 command stdin／stdout／stderr、gprof、350 observation 原流、完整壓縮有序圖與 guards。新 tar 僅把 header timestamp 正規化為 0，逐檔 bytes／permission 已與 CI ZIP 靜態比對全等。
- `CI_RESULT.json`、`FORMAL_DRIVER_RECEIPT.json`、`CURRENT_PRODUCT_INPUT_CLOSURE.json`、`CI_MANIFEST.json`：由成功 CI ZIP 直接 byte-copy，沒有重寫 JSON。`CI_MANIFEST` 記的是完整原 CI ZIP 的 6,220 個原檔，不是只記本目錄子集。
- `DELIVERY.json`：各固存檔的 bytes／SHA256、原 CI／artifact／execution 身分與固存範圍。

完整 [artifact 13095888231](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41337519632/artifacts/13095888231) 為 92,447,830 bytes，ZIP SHA256 `29ba48759a323cce3ab2dfbe8773f2d49597dcd762c0bc1a6dd00682a282e0de`，保留至 2026-12-01 18:42 UTC；完整 ZIP 也保存在本機交付目錄。它另含 wrapper／Git current-input streams、原工具、原 R8 tar 與容器 setup 原流。原 R8 tar 本身早已在 Git 中固定，這裡不再重複 31MB 原包。

資料固存以 `[skip ci]` 提交，避免對已完成證據重跑產品；沒有改測試、門檻、原工具或正式結果，也沒有改 #338 的產品 head。
