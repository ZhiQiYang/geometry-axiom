# #118：既有測試成本與重複工作

來源 main：`5e0e92b850209e9e2895612148694c1d1e1e4815`。
本輪只新增自有 diagnostic tools／報告；PR149 的原 head `2c3ba8faf907737e33e4c1432e22525da284a75e`
保持不動。未修改 runner、workflow、產品、floors、golden、skip、timeout 或 freshness。

## 優先三項，可交唯一 owner 實作

| 優先 | 根因與證據 | 最小改善與保留防護 | 實測界線 |
|---|---|---|---|
| 1 | workflow 六 browser jobs 各 `npm run build`；package.json:7 每次編 core/bridge/model-base。browser dependency closure（含 CDP P76）完全不消費 `.build/core`。 | 加 browser build target，只編同 flags 的 bridge/base；workflow browser 呼叫該 target，原 npm build 的一般入口保留。六個 jobs、全部 browser guards／golden／截圖、fonts、timeout、stack 不變。 | **可移除六次無 consumer core 編譯**，十二次各 runner 必要 bridge/base 編譯保留。當前 CI compiler 時間與實作後節省秒數未測。 |
| 2 | binaries.py:222–236 的 `_scan_shared` 對兩個 native 目錄各用三個 rglob pattern，共六次遍歷；47 Python suites 全部收到五個 populated overrides，靜態 preflight235次，含47次同 bridge alias。 | 優先僅把 enumeration 改成每個 native 目錄一次遍歷，完整保留原 file set／case／symlink／排除語意；每次仍 hash 當前 source bytes 與 raw executable，不 cache fresh verdict。 | warm source fingerprint中位11.46–15.11ms，其中 scan6.29–6.80ms；alias去重估約0.56s。不是 full-run 實測或主要慢因，也未量測新 scanner收益。 |
| 3 | test_serve.py:177,723 用 `serve_forever` 預設0.5s poll；正常成功路徑12個 test-server生命週期。shutdown可能等到下一次 selector poll。 | 只改這兩個 test thread 的 `kwargs={"poll_interval":0.01}`；保留每個 HTTP oracle、0.1s BRIDGE_TIMEOUT、urllib／join deadlines、negative Event.wait ordering斷言。 | 最終有等待上限的三組無監聽port socketpair probe：default shutdown中位0.500619s，0.01設定中位0.010028s。這是**合成 idle 機制**；真 test_serve 實作後節省秒數仍未測。 |

這是 owner proposal，沒有修改上述共同檔。第一項 caller proof：
workflow:62–63 build、:74–75只注入bridge/base；cdp:82、space:625、documents:22只spawn Chrome；
parameter_workflow_test.js:86–96（P76）只下載／讀取／匯入JSON，截圖寫TEMP；
serve.py:57–66 launch GEOMETRY_BRIDGE，model route:477 → modeling engine:309 → base.py:106,113
launch GEOMETRY_MODEL_BASE。polydraft_test.js:987,1002使用TEMP registry core，屬native aggregate，
不被CDP require。browser所需的bridge/model-base不得一起刪除。

第一項推薦維持單一 compile flags 來源，例如共用既有 build target命令，再組成
build（core＋bridge＋base）與 build:browser（bridge＋base）；不要讓兩套bridge/base flags長期漂移。
拒絕直接跨VM沿用 `.build` 檔名。跨job artifact reuse須另外驗同SHA／平台／命令、原sidecar、
raw SHA、納秒mtime與execute mode，不能補發sidecar或放寬mtime；收益與archive roundtrip未測。

第二項反例必留：新增／刪除任一 .c/.h/.inc、uppercase extension的Windows matching、
vendor/node_modules排除、root includes及symlink語意；原同尺寸還原mtime tamper、hash期間替換、
copied-sidecar／cwd-PATH、build前後與receipt pre/post/copied-child guards都仍要拒絕。
按suite.needs縮小overrides是另一候選：47suite全量235 checks，declared-needs-only counterfactual63，
但transitive／instrumented／spawn依賴未實測完整，所以本輪**不改傳入集合**。

## 已有耗時：測試本體與等待不能混算

native封存實測 head：`3019c036c74633a0379714180fa6d68af067d88e`；不是本輪main跑測試。
整個命令363.113s，suite process clocks合計332.1s。sidecars記五支必要cold build stage
10.3＋6.4＋0.4＋6.6＋7.0＝30.7s，含smoke／guards；compiler-only未測。
suite clocks外約31.013s差額不能全叫idle、build-only或可刪成本。正常fresh registry
已沿用，不會compile；#122的unused native prebuild已合併，不再重提。

| 封存suite | 子行程wall（console四捨五入） | runner inclusive | unittest run（含所有fixtures/cleanup） |
|---|---:|---:|---:|
| reader41 tests | 87.7s | 87.60s | 87.465s |
| model-update26 tests | 58.7s | 58.65s | 58.522s |
| serve34 tests | 13.1s | 13.01s | 12.883s |

reader約26.4% suite wall，確為最大的封存suite，但現有Python logs無逐test/phase timing。
它有多種SSOT/DOM/錯誤模板/rebuild oracle與真Node renderer，不能把87.7s當sleep或可省額度。
model-update有舊record native replay、新scene／graph／preview及故障注入實編，也不能算成
單一compiler成本。不同instrumented或mutant source不能用普通bridge替代。
下一步應先有界記錄reader的parent test及rebuild/validate/render phase，再合併真正重複工作；
不得cache expected或去掉負例。這輪未改共同reporter以加timing。

Node log已有item timing，含parent/subtest inclusive時間且檔案可能並行；本工具不相加它們。
`wait(timeout=10)`是上限，`Event.wait(.05)`可能是必要negative ordering oracle，
故障child `sleep(10)`會被timeout/output-cap提前kill；字面秒數不等於實際等待，不能相加。

## 全量與focused：有重疊，保留guard

full CDP包含assembly150／grid182斷言，CI另有focused jobs，故存在重疊；但focused提供
早期回饋及full前段失敗時的獨立局部證據。本輪不刪job／斷言，也不將重疊數乘成省時。
若owner另批縮default matrix，要同時保留required full CDP完成／83段2054 golden、
承接assembly/grid截圖、審查branch-protection check名稱；不能用假pass或skip取代。

space full202與timber79都跑font-layout19及setup/health；timber主流程48與source guards8
**不在space full中**，timber獨立入口保留。documents與formal owner gates也保留。

#123已合併logs：FROM_P31 baseline首次620s exit1／未完成；第二次1055s與patched1089s
exit0／partial761斷言，兩份完成log均有exception count1且未比full golden。
SPACE_FLOW_ONLY baseline58s／patched59s是partial43，非full202。
前後補丁對照與失敗重跑不是已確認可刪成本；當年binary內容對來源未能獨立核對的限制仍在。
P35-only開發入口是候選（當時目標14，尾段761），但section成本未測；最後仍須full gate。

## 自有工具與測量方式

`receipt_costs.py`只讀既有table／JSON／logs與source AST，不import repo tests，不啟動native/browser。
它區分source SHA、aggregate evidence SHA、browser baseline label，所有未知phase成本保持null。
保留FAIL／not-run／失敗partial／missing terminal，不升格acceptance；舊per-suite檔不套到not-run列。
Node timings不相加。輸出拒絕覆寫既有檔。

```sh
python3 tests/cost_audit/receipt_costs.py --self-check
python3 tests/cost_audit/receipt_costs.py --evidence-sha 3019c036c74633a0379714180fa6d68af067d88e --aggregate-log /workspace/pr136-3019c036-review/receipts/08-aggregate.log --aggregate-receipt /workspace/pr136-3019c036-review/receipts/08-aggregate.json --suite-dir /workspace/pr136-3019c036-review/suite-logs --browser-baseline-sha d6b4b450d741fcbbfd75c51631915d3082926990 --browser-log geometry-web/docs/issue123-c-pending-tests/measurements/t3_cdp_baseline.log --browser-log geometry-web/docs/issue123-c-pending-tests/measurements/t3_cdp_baseline2.log --browser-log geometry-web/docs/issue123-c-pending-tests/measurements/t3_cdp_patched.log --browser-log geometry-web/docs/issue123-c-pending-tests/measurements/t4_space-flow_baseline.log --out /workspace/issue118-cost-ledger-5e0e92b8-20261006-final.json
python3 tests/cost_audit/shutdown_poll_probe.py --out /workspace/issue118-shutdown-poll-20261006-bounded.json
```

以上工具命令exit0。poll probe三次每種設定，shutdown放daemon worker並有限join；
清理只wake socketpair，不再同步呼叫無限wait的shutdown。只用socketpair／stdlib BaseServer，無TCP監聽port、
HTTP request或產品服務；native純讀microprofile共0.4s，五次每個fingerprint及三次raw hash，
只讀來源與現有binary bytes，不發fresh憑證、不啟動exe，也未比對既有binary與5e0來源／sidecar。
原native profiling scratch helper封存為 `evidence/native-profile-original.py.txt`，含hardcoded output／
可覆寫scratch檔，僅供審查，不是canonical diagnostic入口。logical source reads258.7MB是靜態
全量preflight推導，非physical disk I/O或實際全庫counter。
詳細 [cost ledger](evidence/cost-ledger.json)、[native raw measurements](evidence/native-profile.json)、
[poll samples](evidence/shutdown-poll.json)、[source 同一性](evidence/historical-main-equivalence.json) 與
[獨立 tool review](evidence/tool-review-final.json) 由 [index](evidence/index.json) 記錄逐檔SHA-256。
browser reviewer的可選default-matrix減項未採用；本proposal保留全部六個jobs。

## PR149 postmerge小驗與未驗

精確merge `5e0e92b850209e9e2895612148694c1d1e1e4815` 的新registered reporter gate：
`python3 tests/_unittest_runner.py tests/test_unittest_runner.py --json-out /workspace/issue118-postmerge-5e0e92b8-20261006/gate.json --log /workspace/issue118-postmerge-5e0e92b8-20261006/gate.unittest.log`
實際exit0、1 pass／0 fail／0 skip、2.825066s。registry errors=[]，loader/expected count=1。

未重跑全庫／browser作計時，沒有新產品main-flow／Windows/GDI／WSL／hosted-CI驗收。
三項owner改善均未實作或測量整體收益。所有舊held packages保持不動，未發布它們。
