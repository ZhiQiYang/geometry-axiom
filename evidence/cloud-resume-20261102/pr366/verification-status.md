# #366 新 head 官方 CI 核收完成

固定 PR head：`502a64ff6214dd6060927b7f14643a533536f20d`。本輪只追既有 integration run `41376852060` 與 mutation run `41376852056`，均 attempt 1；沒有啟動重複 CI、push、留言、產品或 SSOT 修改。

## 已核收

- API snapshot、job 原 log、官方 artifact ZIP 原件及其下載指令／HTTP 狀態／SHA-256 存於本目錄。ZIP hash 逐件等於 GitHub artifact API `digest`，不是只與本地 manifest 自洽。
- mutation 的 workflow／原架構／已完成四片 core checkout 皆為 `502a64f`；本次不沿用 `df347` 綠燈。
- integration 實際 checkout 是 PR 合成 merge `7d2a1927e15d3c0d59b20fa6618005f19c4a6c56`，parents=`5775a9e9e46bca801a9a70aaeafcdab9f597bc4d`＋`502a64f`。兩個 commit 的 Git tree 均 `910665aa55b5be4830de2f729a7aca5db1cbe8cc`。不把合成 execution SHA 寫成直接 head 執行。
- 原架構三命令 receipt、raw stdout/stderr、全部 604 inputs 與 scanner/test/source LF hashes 相符；334 owned、270 exclusions、798 edges、0 diagnostics；原兩支 unittest 為 205 與 18，exit 0、零 skip。核收命令 exit 0；沒有在本機重跑架構產品 tests。詳 `architecture-audit.json`。
- native 三片官方原件由原 `tests/native_shard_receipts.py` 重驗 exit 0，與官方 aggregate 完全相等：230 suites，77／76／77 無交集且聯集完整；5340 counted、5339 pass、1 allowed Linux GDI skip。獨立本地 Git metadata 引用真合成 commit 和原 objects，使原工具辨識真 execution SHA；source 本身 HEAD 仍為 `502a64f`。詳 `native-reverify-receipt.json`。
- 官方原件及本地原 `tests/native_sharding_mutation_check.py` 皆驗出基準／移除 `c:integrity`／恢復為 0／1／0；紅為指定 coverage test 的 `AssertionError`，1 failure、0 error、0 skip。只執行工具級 coverage 負控制，未執行 native suite 或下載的 ELF。詳 `native-control-receipt.json`。
- 七片 mutation artifact 的官方 ZIP digest、三檔 manifest hash、二進位 bytes、sidecar、ledger、原 strict 均通過。4 core＋3 bridge 指派為 18／18／17／17＋18／18／17，聯集精確涵蓋 123 records、120 active，沒有重複／缺漏／額外 ID。結果為 114 killed、1 crashed、5 equivalent、3 retired；survived／invalid／stale／blocked／unrun 皆 0。七片均屬本 run／attempt／head；probe M01／M02／M03／M04／M61／M62／M63 的官方 job log 均證明 bad-cache stale 1 與恢復 stale 0，manifest strict exit 1。詳 `mutation-shard-audit.json`。
- 全部 53 bridge records 的 baseline／mutant／restored stdout 結構化 marker 已重新解析並與 ledger.result 相等：159 次對比，共 109 個獨立 oracle raw 檔案。逐次建置／oracle stdout 與 stderr 的原 bytes hash 亦由原 supervisor 驗過。
- 原 `.github/scripts/mutation_evidence.py verify` 在另一接收環境重驗 exit 0，只讀二進位 bytes、未執行或重編下載的 ELF。原 full-table strict exit 0；新產 ledger 和 summary 均與官方 aggregate 逐 byte 相同。ledger SHA-256=`102c541d59a82e18ba44c6fc0d1ed8116bc581baf759837f734e6fff1d17a5cc`；summary=`055477f48cc8288dc1f8a4914fa2b97c7c1eec39778de153bd17ebf721fe5a14`。原命令與 stdout/stderr hash 詳 `mutation-verify-receipt.json`。
- integration 六組 browser 原 log 已核收：assembly 150、grid 356、documents 47、space 242、timber 79、canvas 2267，皆 failed 0。這些是各組原 assertion 計數，不能當作去重後完整 E2E 個案數。canvas 為完整 scope，無 filter／modifier、skip[]，85 段 golden 逐段相符；runtime fresh。canvas 的 1 個 uncaughtBrowserException 為 P38 明示注入 `fb-auto-probe`，raw 為 EXPECTED，沒有 UNEXPECTED；P53 transport 與 P61 lost-reply 訊號也已對照原測試受控注入與後續通過斷言。詳 `independent-native-browser-review.md`。
- 終態兩個官方 run logs ZIP 亦保留；其中 20 個 whole-job log 與各 direct job logs endpoint 下載原件逐 byte 相同。integration logs ZIP SHA-256=`e6c803301da2b76ae36ef23f0733e94f26f3183aa8cc9669c4eb2c482eb92d94`；mutation logs ZIP=`22c15e146713d24366440fe57e8903ac1090861d8360e47bc7241271dc571383`。詳 `official-run-log-audit.json`。
- 來源工具對抗審查未見足以阻擋目前官方 run 的缺陷。`verify` 不自行強制 run/attempt/probe；本輪由 API、manifest、七片 log 額外核對，bridge raw 與 ledger.result 亦已全量對比。詳 `source-tool-adversarial-review.md`。

## 終態與未驗邊界

終態 snapshot `api/20261102T025323Z`：integration `41376852060` 與 mutation `41376852056` 均 completed／success；各 10 jobs、總計 20 jobs 全 success。21 個 artifact ZIP 全部核對 GitHub API digest；兩個官方 run log ZIP 與 20 個 job log 原件皆保留。這是新 head `502a64f` 的核收，不沿用舊 head `df347` 綠燈。

`workflow_dispatch` 在工具進入 default branch 前未實測；本輪不改 default branch、不 merge main 以繞過入口條件。

未在本機重跑 native／架構／browser 產品 suites，也未執行下載的二進位；只有純證據 verifier 與原拆片工具負控制在本機執行。本輪未做截圖視覺 QA；其官方 bytes 與 digest 已保存。source 維持 `502a64f`，未修改產品／SSOT、未 push／留言／啟動 CI。
