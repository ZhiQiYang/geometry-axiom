# X7：大場景效能預算與 R03 預覽第一片

固定量測基底：`4c4028f8f80f09963f14a46062cbfcf8db76637b`。任務來自 issue #487 工作包 X7，設計交付在 issue #386。這份文件記錄本機原生量測與可重跑守門；正式 CI 成本、真 Chromium 延遲、Windows、實體手機及使用者驗收未取得。補丁本身沒有實作 PR，不據此新增 L2／L3／L4／L5 聲明。

## 場景從哪裡來

`tests/diagnostics/x7_scenarios.py` 用真產品協定生成下表。產物位於執行時的新目錄，不提交大型 `.scene` 或預先算好的產品輸出。

| key | 完整角材數 | 生成與批次操作 |
|---|---:|---|
| room53 | 53 | 3740×3301，明選 `flat-ceiling/2`、915×1830×6 板材、27×33 角材、gap 2、X 8。量真正 R03 預覽及一筆確認。 |
| f1_111 | 111 | 現行 F1 oracle 的 layout 索引 7（零基，即第八個排法），凹形且含 400×400 孔；既有 `core-probe/gen_scenes.py` 產生公共 DSL，再由真 bridge 載入。批次是整檔 `load-prepare/load-confirm`。 |
| house500 | 500 | 三個完整 F1（333）＋7000×3301 的 83 支＋8000×3000 的 84 支，五個分離房間、15 條 guide；最後一批量 416→500。 |

現行 F1 八排法為 95、97、96、98、108、110、109、111；歷史「約 116」不能冒充現行結果。保留真 F1 的凹口與孔，沒有換成 bounding box。main R03 對它仍回 `UNSUPPORTED_SCOPE`，所以 F1 的整檔採入與另外兩個場景的模板生成分欄記錄；本片沒有完成凹室、孔或多面整批功能。

獨立 checker 從現有 oracle／golden 取期望，從原生 origin、三個軸、A／B／length 重建每支八頂點，核對全部 IDs、角色、宿主、包絡及無體積重疊。500 是五份完整骨架，沒有砍掉末端副骨湊數。preview 只有新建 handle；正式 ID 在 confirm 後才讀，不從產品幾何反推期望。

## 重跑

於 repo 根目錄，使用新的輸出目錄：

```sh
python3 -B tests/binaries.py build bridge
python3 -B tests/diagnostics/x7_scenarios.py --out /tmp/x7-scenes
python3 -B tests/diagnostics/x7_benchmark.py --fixtures /tmp/x7-scenes/browser-bundle.json --out /tmp/x7-measure --repeats 5
python3 -B tests/diagnostics/x7_budget.py --report /tmp/x7-measure/report.json --budget tests/diagnostics/x7_budgets.json --out /tmp/x7-budget-verdict.json
python3 -B tests/test_x7_performance.py
python3 -B tests/diagnostics/x7_withdrawals.py --fixtures /tmp/x7-scenes/browser-bundle.json --out /tmp/x7-withdrawals
```

生成器與 driver 拒絕非空輸出目錄，raw 排他建立，不覆蓋首跑失敗。命令有有限截止，子行程失敗、protocol 失敗或 stderr 非空都不能成為成功樣本。沿用既有原生 16 MiB stack 前提；這片不處理 H2，也不改任何既有時限。

`test_x7_performance.py` 自行重產場景，再編譯測試專用 observer closure。可設定 `GEOMETRY_X7_ARTIFACTS` 保存原件，或用 `GEOMETRY_X7_FIXTURES` 指向先前真生成、通過 bytes/SHA 核對的 bundle。正式量測使用未插 observer 的官方 fresh binary；完整驗證次數與故障注入使用隔離 observer，不把其速度混入預算。

## 計時方法

- 原生 `wire_ms`：發送及 flush 到讀到完整 JSON 行，含 native 與 pipe，JSON parse 另記。
- 載入：常駐 bridge 完成 reset 後的 `loadfile`。啟動／reset 數字保留 raw，與使用者操作分開。
- 每個 benchmark 樣本啟動新的 bridge，第一個 completed-scene 載入是新原生程序。生成器內 `cold_bytes`／`X7_CANONICAL_COLD_ROUNDTRIP_BYTES` 的標記只核同一程序重新解析保存內容；不把那個內部標記當成 App 冷開或清除 OS 檔案快取的證據。
- 原生另存：dump、JSON decode、UTF-8 寫檔、flush、fsync。量的是 `.scene`，不是 `.gcanvas` 附件與 OS picker。
- 料單：真 `timber-schedule.js`，依全部宿主計算，核全部成員及來源值。Node 啟動、讀檔、JSON parse 不在 derive／CSV 時間；首個冷 module 樣本保留。
- 五輪不丟第一筆，不丟慢值。中位數僅用來說明，守門逐筆檢查最大值。五個樣本的 nearest-rank p95 就是最大值，不冒稱估出了長期尾端分布。

量測機器為 Linux x86-64、AMD EPYC 9V74。前後使用同一 bundle，量測時沒有同時編譯或跑另一個 benchmark。原始命令、binary SHA、每筆數字、回覆 bytes/hash、子行程結束碼與 stderr 保存於交付原件；這些是本機一致性證據，不是可信正式 CI 收據。

## 五輪觀察

下表是中位數，單位 ms，每格為基線 → P。

| 操作 | 53 | F1 111 | 500 |
|---|---:|---:|---:|
| 載入 | 285.768 → 281.079 | 198.393 → 216.834 | 4287.417 → 4297.244 |
| R03 預覽 | 51.973 → 25.147 | 不支援 | 4524.770 → 1099.145 |
| R03 確認 | 30.298 → 38.466 | 不支援 | 370.743 → 359.008 |
| 整檔準備 | — | 175.248 → 194.600 | — |
| 整檔確認 | — | 14.130 → 12.902 | — |
| undo | 9.688 → 18.721 | 11.691 → 4.353 | 18.644 → 12.664 |
| redo | 1.126 → 1.045 | 1.014 → 1.105 | 1.133 → 1.204 |
| dump | 1.018 → 1.045 | 1.096 → 1.305 | 3.905 → 3.974 |
| objects | 0.129 → 0.132 | 0.188 → 0.245 | 0.752 → 0.788 |
| references | 1.957 → 1.793 | 2.523 → 3.022 | 16.949 → 17.337 |
| `.scene` 另存 | 2.462 → 2.345 | 2.956 → 2.735 | 6.334 → 6.356 |
| 料單 derive | 0.116 → 0.176 | 0.174 → 0.154 | 0.548 → 0.425 |
| CSV | 0.695 → 0.370 | 1.146 → 0.902 | 3.195 → 2.778 |

500 預覽中位數減少約 75.7%，53 約 51.6%。載入未改；小操作與 fsync 有抖動，不能把所有中位數差異都歸因於 P。前後三場景五輪的 references、保存 scene，及各場景 CSV 原件合計 33 組比較全部逐 byte 相同。真正 full-validation counter 與穩定輸出比較另證明修正的因果關係。

## 新操作預算

`x7_budgets.json` 是明列且可審查的上限來源，不是 CI 成本。預覽取 P 五輪 max；其餘操作取基線與 P 十筆中的 max。上限為 `max(25, ceil((max_ms × 3 + 5) / 5) × 5)` ms：保留三倍相對餘裕、5 ms 絕對餘裕、向上取整至 5 ms，小操作至少 25 ms。這是本機初始預算；正式 runner 超限時須附原始數字調查，不能自動學習較慢上限或忽略慢樣本。

| 操作上限（ms） | 53 | F1 111 | 500 |
|---|---:|---:|---:|
| bridge_dump | 25 | 25 | 25 |
| bridge_objects | 25 | 25 | 25 |
| bridge_references | 25 | 30 | 70 |
| framing_confirm | 140 | — | 1355 |
| framing_preview | 95 | — | 4010 |
| import_confirm | — | 80 | — |
| import_prepare | — | 640 | — |
| native_load | 1180 | 795 | 13430 |
| native_save_as | 25 | 105 | 70 |
| redo | 25 | 25 | 25 |
| schedule_csv | 25 | 25 | 25 |
| schedule_derive | 25 | 25 | 25 |
| undo | 70 | 65 | 65 |

checker 要求全部三場景、33 個操作齊全，按 raw 重算統計、逐筆比上限，拒絕缺樣本、NaN／Infinity／負數／布林數值、錯誤命令、非零 child、stderr、不同 binary、改計時邊界與不相符 bytes/hash。保存計時值只在主 report，沒有第二個獨立時鐘；保存 bytes 仍核對。合成 checker 自測中的 1／10 ms 是反例，不是這張表的量測。正式套件跑每操作三筆共 99 筆，全部必須通過。

本片不重寫舊 deadline、count、golden 或 byte pin。`tests/suites.d/py__test_x7_performance.json` 經 `--init-suite` 建立，宣告需要 bridge 與 Node，expected 保持 `pending-ci-census`。套用端須先跑 Native suite measurement，再由可下載官方 artifact 的 grokbot／本機 Claude 用 `--import-suite` 產生並原樣採入計數與成本，才跑正式全集。Mutation evidence／Architecture evidence 亦由正式 workflow 重產；本機不手填任何收據。

## 三個慢點與第一片的邊界

基線 500 的排行是預覽、載入、確認。設 n 為 World 現有角材，m 為新 marks，V(n) 為一次完整驗證。

1. R03 evaluate 原先每個 mark 的 `spec` 與 `guide` 各完整驗證，約 `(3 + 2m) × V(n)`。`wood_world_validate_members` 有 O(n²) 配對；接觸事實／索引反覆建立還有 O(n² log n) 路徑，不能把 V 視為常數。原生計數量到 53 的 19 次、500 最後一批的 17 次。
2. 載入已合併連續 timber/place，並非所有行都全驗；但 spec/guide 仍逐行驗，R03 保存內容含這些定義，仍有約 O(m·V(n)) 成本。後片要保留 scene replay 的首錯與原子性，再研究群組邊界。
3. 確認仍須依 I8a 完整重驗，成本含來源重建、配對與接觸面。後片改善單次 V(n)，不能刪除確認檢查。既有 footprint／anchor memo 已在，不能把重做這層 cache 當新修正。

第一片僅修改 H adapter 的 marks staging。原 parser、spec 名稱與 ID 分配、來源表達式、W 計畫、schema／政策指紋、最後逐支八頂點與 R43 支承檢查均保留。初始化宿主、from-fill grid、合併後的 marks、完整 timbers 各完整驗證一次，共 4 次；確認再驗 1 次。

checkpoint 使用既有指標型 WorldSnapshot，沒有新增以值 World 堆疊框。已有 deferred、非精確 active candidate、零 mark、bay-repeat instance 均保留原路徑；可選 snapshot 取不到也回原路徑。fast 嘗試暫時 mute，失敗時清除試算 resolver／source graph、還原 World 與診斷，再走原序 parser，避免把較早的引用錯誤換成較晚的解析／容量錯誤。測試確實注入早期 missing-reference 與較晚 malformed spec；snapshot 測試是令取得函式回傳 NULL 的故障注入，沒有宣稱發生真 OS OOM。

`tests/test_geo314_commit_paths.py` 的 **REVALIDATE_SITES 具名契約遷移**只新增 `framing_template_marks` 一個呼叫點。原 evaluate 的兩個呼叫、確認與所有 publish／replay 分類均留；新點沿用 evaluate 已設的 `c->before` 與同一 H 候選。這是新增完整驗證點的精確登錄，不是減少原斷言、允許任意新路徑或放寬接受範圍。

## 在途整合與後續

基底獨立於未合併 PR。已讀 #487 列出的 17 張在途 PR 全部檔案清單。#477 head `22e4f85d0e076034ee083fb183c6a9f1a708de7a` 同檔增加 L 形與 member order；整合須保留 `notch.order`，不能用本片重蓋。#478 head `233097379ecdb4873fa67939686c3bdcfbf7fe30` 同檔另有 R-butt shift spec/guide loop；本片不自動套用 batching 或把其成本當已量測。#471 head `983d2a5be9aff7d365c482fa3a919859c71e5829` 的 H1 history spare slot 不在本片範圍。後續新版本與 X5 要重新核對自己的 oracle、錯誤順序、完整驗證次數及耗時。

S1 套用結果回來後再出 S2 載入、S3 單次驗證／查詢。純 references 的逐支接觸面重建、dump 與 fingerprint 重複序列化亦有可改善處，但本次原始數據顯示它們並非前三慢。

## 真 Chromium 交接與未驗

見 `tests/diagnostics/x7_browser_measure.md`：共用同一 bundle，1400／390 px 各三圈，真 UI 事件、新請求、新狀態與兩個新 animation frame；完整記錄首跑失敗。這是獨立診斷入口，沒有新增 canvas module、沒有改白名單／順序／歷史 pin。未實跑前不填前端實測預算；30 秒診斷截止也不等於效能驗收。

未驗包括：真 Chromium 流程及延遲、正式 CI 與新 suite 成本、Windows／實體手機／OS 原生對話框、在途新增模板版本、bay-repeat 的加速。R03 既知的派生宿主顯示與尺寸、X 使用處等缺口仍照需求帳，不因原生性能綠燈變成已驗收。公理層.md 及需求帳層級沒有修改。
