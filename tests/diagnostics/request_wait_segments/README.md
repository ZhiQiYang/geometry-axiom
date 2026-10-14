# #209：15 秒逾時的分段量測

看板指定任務 12，依 [R1 研究](https://github.com/ZhiQiYang/geometry-axiom/issues/209#issuecomment-6161512975)。完成於 2026-10-14（Asia/Taipei）。**只量測，不實作修復。**

受控重現顯示：同一個「服務未在 15 秒內回應」可由等待 bridge 鎖，或等待原生回覆造成。後續已進入 error 的呼叫重複顯示相同訊息，其中多筆根本沒有 fetch，不能算成另一筆慢請求。renderer 20 倍節流單獨未重現逾時；這不代表歷史 Windows/WSL 負載已排除。

## 範圍與環境

- 產品基準 main：`f9ada2201fedd0c962b9384f1c83ed53d3b7f876`。七組執行時工具提交：`2faa29dbf6a890ae88d5fc265a6d03e634c7f606`；每組另存實際執行工具與 SHA-256。之後僅強化離線分析器、附報告及證據。
- Debian 13.6 / Linux x86_64、Python 3.12.14、Node 24.19.0、Chromium 154.0.8037.57、Playwright 1.62.1、GCC 14.2.0；原生繼承 `ulimit -s 16384`。
- 現有工具目錄無 Browser plugin，使用已安裝的 Playwright 與 system Chromium，沒有安裝依賴。每組獨立 server、原生程序、port、瀏覽器 context、暫存 feedback；不連使用者服務。
- `/runtime` 逐組確認 root、PID、fresh=true、版本 `afe9bc3739109bcf734a82dc4265b1ac03a59d9454f3e9df4335773a7e16d90a`。原生 binary SHA-256：`b49dccd56ee3729d48dcf5f8a908ae619fdd994d91a59cd70af691034adc76e3`；registry 確認來源與 binary fresh。
- 僅執行 `cdp_test.js` **P7 的原始 insR 表達式**與原 settle helper，經原 DOM-event 操作凹口。保留原五項 oracle：select、panel=true、verts=8、fixity=8、ortho=true。沒有跑完整 P7/P52、完整 canvas、真實滑鼠或 WSL 全量。
- 新增檔案只在本診斷目錄及 evidence。`geometry-web/`、`geometry-core/`、`current_geometry.c`、SSOT、guide、BACKLOG、決策佇列、SketchUp 與 main 基準的 diff 為空；不改產品逾時、收據、斷言或 expected。

## 方法

`server.py` 匯入未修改的 `serve.py`，轉送原 lock、stdin、queue、fresh、HTTP handler 呼叫，記錄 server `monotonic_ns`、PID、TID、診斷 request ID、命令、native PID、等待與執行時間。正確性仍由原 handler、原 mutex、原收據及原 bridge 處理。lock 的量測包含少量插樁開銷；fresh 扣除 lock wait 的數值是約數，沒有把來源 I/O 各檔另拆。

只有獨立診斷服務有 `/__diag/hold`：取得實際 runtime/receipt/bridge lock 後 ACK，或確認子程序父 PID 後 SIGSTOP 原生程序，18 秒後 SIGCONT。ACK 在呼叫原 apiRequest 之前取得，因此不佔用其原始 15 秒計時。3 秒 bridge 控制組確認持鎖釋放後正常恢復。renderer 節流使用 CDP 20 倍，只限制 renderer，並非整台主機。

瀏覽器 wrapper 轉送原 apiRequest、fetch 的 body、AbortSignal 與 response，只加診斷 header，記錄 `performance.now()`、phase、真實 fetch 拒絕與回傳。mutation 保留原 requestId，復原僅走原 receipt 查詢，沒有重送修改。

兩個程序的時計**不互減**；用診斷 ID 對應，各自計算耗時。signal 在 fetch 已回 headers 後仍可能觸發，分析器只把實際 `fetch_error` 算逾時，不把這些晚到 signal 算失敗。每組最後等實際 load_released、所有已接受的 `/api` handler 結束，再確認原生仍存活、bridge_failure=null，才關閉自己的服務。

## 七組結果

| 組別 | P7 五項 oracle | 真正逾時 fetch | 最終 phase | 說明 |
|---|---:|---:|---|---|
| baseline | 通過 | 0 | ready | 凹口 8 頂點、8 fixity、正交 |
| renderer-cpu20 | 通過 | 0 | ready | 單獨 renderer 節流未重現 |
| bridge3 | 通過 | 0 | ready | 3 秒持鎖後原流程完成 |
| bridge18 | 未完成 | 2 | error | source-inspect、並行 dump 等 bridge 鎖 |
| native18 | 未完成 | 2 | error | source-inspect 等原生回覆；並行 dump 等前一筆釋鎖 |
| runtime18 | 未完成 | 1 | ready | 原 receipt 先到，取消尚未進入核心的 mutation |
| receipt18 | 通過 | 1 | ready | 原 mutation 完成，原 receipt 取回同一結果 |

七組 server exit 均 0、原生清理前均存活且無 bridge_failure、無 harness_error。實驗 runner exit 0 表示量測完整，**不表示四個故障組的 P7 都通過**。所有 console/pageerror 清單為空；原表達式的兩種例外由 harness 保留在 result.json，不吞掉成成功。

## 六筆逾時，逐請求列出（毫秒）

`—` 表示未進入該階段，不是 0。`S` 是原命令 `line surface 1 origin 0 0 0 u +x v +y outline 0,0 200,0 200,100 0,100`；完整小數與 fresh 總耗時在 [timeouts.csv](../../evidence/request-wait-segments-20261014/timeouts.csv)。

| 組別 / ID / 命令 | 瀏覽器 fetch | runtime 鎖 | receipt 鎖 | bridge 鎖 | stdin write / flush | 回覆 queue | HTTP 寫回嘗試 |
|---|---:|---:|---:|---:|---:|---:|---:|
| bridge18 / 26 / source-inspect | 15002.000 | — | — | 17999.715 | 0.016 / 1.250 | 0.089 | 0.687 |
| bridge18 / 28 / dump | 15000.300 | — | — | 17466.017 | 0.011 / 0.012 | 0.898 | 0.253 |
| native18 / 26 / source-inspect | 15000.300 | — | — | 0.012 | 0.008 / 0.008 | 17997.636 | 0.291 |
| native18 / 28 / dump | 15000.400 | — | — | 17482.396 | 0.067 / 0.027 | 1.850 | 0.141 |
| receipt18 / 6 / S | 15000.600 | 33.026 | 17898.452 | 0.019 | 0.009 / 0.027 | 14.395 | 0.219 |
| runtime18 / 6 / S | 15000.800 | 17994.792 | 0.020 | — | — / — | — | 0.162 |

六筆都在原前端約 15 秒拒絕 fetch；server 約 17.467～18.052 秒才結束 handler。六筆原連線寫回均 BrokenPipeError，瀏覽器未收到 headers；表列寫回是**失敗嘗試時間**，不能冒稱成功傳遞延遲。bridge/native 組在清理前確實收到非空原生回覆，含 bytes、SHA-256、arrival timestamp；stdin/queue 並非因提前殺程序而缺失。這次沒有重現 stdin 寫入阻塞，也不能從本次排除其他負載下的 pipe 問題。

readonly 的 source-inspect/dump 原本就跳過 fresh，亦沒有 mutation 收據，因此前四筆 runtime/receipt 欄為未進入。receipt18 的 fresh 總耗時 86.993 ms，其中 runtime wait 33.026 ms。runtime18 的 fresh 總耗時 18051.186 ms，其中 runtime wait 17994.792 ms，剩餘約 56.395 ms；本次長時間是**人為持有來源鎖**，不是量出來源檔案讀取本身耗時 18 秒。

### 收據與尚未送出的呼叫

runtime18：原修改 fetch-6 在約 15 秒逾時；fetch-7 以**同一個** requestId 查 receipt，約 10.9 ms 收到 headers，原 apiRequest 回「操作未送達，場景未變更；請重新操作。」並保持 ready。晚到原請求沒有 stdin/queue，未執行 surface；原 P7 繼續找未建立的 UI，出現 `null.click`。這是取消後的次級測試錯誤，不是核心崩潰。

receipt18：fetch-7 同一 receipt 約 3014.8 ms 收到 headers，原 apiRequest 回 ok=true，P7 完成；原命令只送往 bridge 一次。不能把每個底層 15 秒 fetch abort 都當成最終 connection error。

bridge18 與 native18 各有 **5 筆在 phase=error 後、fetch 前被擋住**：原 P7 的 `line boundary 1 outline 0,0 50,0 50,50 150,50 150,0 200,0 200,100 0,100`、`boundary 1`，以及診斷追加的 `dump`、`boundary 1`、`references 1`。五筆均回同一 transport error，實際 fetch 數為 0。並行 dump 則早已在 error 前送出，確實是另一筆約 15 秒的逾時，不能與這五筆混算。原 P7 不檢查失敗讀取便存取 `b.loops[0]`，因此出現次級 TypeError。

## 建議供 Claude 裁決；本 PR 沒有實作

1. 測試端先區分「原請求仍待確認」「已 error」「已取消」：對仍待確認的 UI 用有上限的狀態等待；已 error 時保留第一筆時間線並停止依賴其資料的後續幾何斷言，避免 loops[0]/null.click 掩蓋先因。不能重送 mutation 來讓測試變綠。
2. 產品端下一輪在實際主機負載記錄**持鎖者與持鎖時間**，再決定是否縮短 runtime/receipt/bridge 臨界區或減少不必要的同時查詢。本次證明這幾段能消耗前端預算，不足以證明歷史故障一定由哪個持鎖者造成。queue 等待包含原生運算、排程與程序暫停，不能直接當成純計算時間。
3. 若評估調整逾時，要一起評估前端 15 秒、bridge acquire 30 秒、response get 30 秒各自獨立預算，以及原 receipt 35 秒恢復。這次沒有足夠實際分布可選新數值，亦沒有改任何 deadline、TTL、receipt 或失敗保護。

## 證據與重跑

[證據索引](../../evidence/request-wait-segments-20261014/README.md) 包含完整 raw archive、逐檔 SHA-256、逐請求分析、六筆 CSV、工具 stdout/exit、DOM、截圖、console、網路失敗與環境。原始工具 bytes 隨每組存檔。

Linux 既有 Python/Node/Playwright/Chromium 環境可跑（工具目前使用 `/tmp/geometry-tests/bridge` 及 `/usr/bin/chromium`，不提供 Windows 可攜性宣稱）：

```sh
ulimit -s 16384
python3 tests/binaries.py build bridge
node --check tests/diagnostics/request_wait_segments/browser.cjs
python3 -m py_compile tests/diagnostics/request_wait_segments/server.py tests/diagnostics/request_wait_segments/analyze.py
node tests/diagnostics/request_wait_segments/browser.cjs /tmp/geometry-request-segments-new
python3 tests/diagnostics/request_wait_segments/analyze.py /tmp/geometry-request-segments-new
```

請使用全新 output 目錄；可在 runner 最後參數選單組，如 `bridge18`，分析器則針對完整七組驗證預期的控制與故障表現。新增分析器會拒絕未排空 handler、清理前原生失敗、缺少真正晚到原生回覆或執行工具 hash 不符的證據。

初版 `cohorts/` 的等待以 case 程序啟動為基準，可能在真正負載開始後未滿 18 秒就清理，造成假的原生 EOF/連線中斷。該版及其初步分析**完整保留為失效 pilot**，不採用其原生回覆結論；正式數據只採 `cohorts-drained/`。這是量測工具修正，不是產品修復。每組結束時 root_context.close 的正常清理 EOF 也保留於 raw，不當作清理前的原生失敗。

## M1 審查補強（2026-10-14）

依 [ChatGPT 審查 M1](https://github.com/ZhiQiYang/geometry-axiom/pull/235#issuecomment-6164435921)，分析器另驗證：

- 七組名稱、各組 timeout/blocked 精確為 `(0,0)、(0,0)、(0,0)、(2,5)、(2,5)、(1,0)、(1,0)`；合計六筆 timeout。
- runtime18/receipt18：同一 call 僅一個原命令與一個原 receipt，瀏覽器 businessRequestId 和 server body 的識別一致；receipt 在原 timeout 後發出並成功回覆，HTTP body hash 與原 apiRequest 取得的結果一致。
- runtime18：保持 ready；原命令無 stdin/queue/非空 native reply；同 receipt 先完成取消，晚到原請求才取得 receipt 鎖；結果必為「操作未送達，場景未變更；請重新操作。」。
- receipt18：保持 ready、P7 通過；原命令的 write/flush/queue 各一次、非空 native reply 恰一次；receipt 本身不執行 native，也沒有重送原 mutation。

`check_counterexamples.py` 直接從未變的原 archive 解出七組，僅修改暫存副本。原件由修前與修後分析器皆接受；12 個資料反例均為修前 exit 0、修後 exit 1，且 stderr 指向具名失敗原因。這些反例是合成錯誤紀錄，不是新的瀏覽器或產品失敗。移除 M1（使用原 head `940d25f1` 分析器）會重新錯收全部反例。

```sh
python3 tests/diagnostics/request_wait_segments/check_counterexamples.py \
  tests/evidence/request-wait-segments-20261014/raw.tar.gz /tmp/geometry-m1-counterexamples-new
```

依 [P-107](https://github.com/ZhiQiYang/geometry-axiom/pull/235#issuecomment-6164666788)，完整 native 在隔離 MUTATE_CACHE 下重跑：88 suites、2775 pass／0 fail／1 平台 skip、exit 0。首輪因共用快取 45 個舊 binary 收據不符而 exit 1，原始結果、45 筆快取對照及負向驗證均保留；詳見 [M1 證據](../../evidence/request-wait-segments-20261014/m1/README.md)。兩輪產品／測試程式 hashes 相同，沒有重產帳本。本輪不領取指定任務 13，不修改產品。
