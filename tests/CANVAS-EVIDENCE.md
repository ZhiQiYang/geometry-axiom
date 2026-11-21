# Canvas 分片與原 golden 收據

`GEOMETRY_CDP_SHARD=1/2|2/2` 選擇真正執行的 canvas 連續區段。
分片計畫與 golden 由 `geometry-web/cdp_sections.d/<段>.json` 確定性組成；
`canvas_registry.js` 是唯一讀取入口。原兩個單檔遷移到 `canvas-registry/legacy.*`，
其原 bytes／SHA-256 留作不可變歷史釘，不再是每張 PR 要改的登錄表。
數值入口仍只有 `1/2`、`2/2`，不提供另一套 `legacy`／`extensions` 分片。
沒有此變數時，原 full 與各 `*_ONLY` partial 入口保留原路由。
shard 不接受 partial flags、engineering modifiers 或更新 golden；不能先跑整條再隱藏斷言。

保留 #369 的 P88 後切點、第一片結束時核對的 localStorage、第二片開始時的還原與核對；
每片的實跑段落順序須等於計畫，P83 producer 到 P86 consumer 的同片依賴不變。
`tests/helpers/canvas_shards.js` 在此計畫上綁定當前 golden、harness、原分片驗證器及
require 來源閉包；每片是一個 journal unit。它不另按本體／外掛重新分派執行。
新獨立段由 `canvas_sections/<段>.js` 與同名片段登錄，無須改 `cdp_test.js` 的名單。
片段與模組目錄雙向核對，少片段、孤兒模組、重複、未知欄位、父層 symlink、非 LF JSON 均拒絕。
零 assertion 段也必須實際到訪。既有段的計數、相對順序、hand-off storage 以及歷史原件 byte pin 不變。

原 `cdp_floor` 的每段精確比較、原 assertion 與 wait timeout 不變。
每片比對其擁有的原 golden 投影，聚合再要求完整 key 聯集無重複、缺漏或額外段。
原獨立 assembly/grid 等 browser jobs 不充當 canvas 分片。

## 原件與核驗

CI 的 `canvas-shard-*` 保存父程序取得的實際 exit、runtime fresh probe、source/plan/golden
雜湊、run/attempt、PR head、實際 checkout SHA/tree、完整 stdout/stderr，以及受控 verdict journal。
一個 console.log 內的多個受控 verdict 逐一記錄；journal 與 shard raw 同步寫出，
不以任意 console 文字的勾號計數。沒有 unit end、截斷或第二個 CDP_RESULT 均拒絕。
來源閉包包含全部片段、動態模組及其 require 相依；舊檔名仍作收據中的虛擬 aggregate hash key，
hash 的輸入是工具產生的確定性 aggregate bytes，實體片段與封存原件另逐檔釘 hash。

`browser (canvas) complete coverage` 只接受同一 run/attempt 的兩份成功原件，重新核對 source、raw、
實際 scope、完整 unit/section journal、順序、切點交接與原 golden；通過後才產生
`canvas-complete-coverage` 內的 `summary.json`。原 `run.json`／`cdp.log` 由新的
`manifest.json`／分離的 `stdout.log`、`stderr.log` 取代；不把舊格式原件當作新來源驗收。
下載目錄必須恰含 `canvas-shard-1`、`canvas-shard-2`；缺 manifest、多出目錄或檔案都拒絕。
PR 合成 merge 的 execution SHA 與 PR head 分開記錄，不把任一個改寫成另一個。

跨環境重驗時，先簽出真正的 execution commit，保持乾淨來源；下載該 run 的兩片：

```sh
gh run download <run-id> --repo ZhiQiYang/geometry-axiom --pattern 'canvas-shard-*' --dir <artifacts>
GITHUB_RUN_ID=<run-id> GITHUB_RUN_ATTEMPT=<attempt> PR_HEAD_SHA=<pr-head-sha> \
  python -B .github/scripts/canvas_evidence.py verify --artifacts <artifacts> --out <new-output>
```

此命令只核驗已保存的原輸出，不啟動瀏覽器或重跑原測試。官方 artifact ZIP 的 API digest
仍是外部來源根；自行重寫整份輸出再重算本地 hash 不等於官方原件。

## 純工具控制

```sh
node --test tests/test_canvas_shards.js
python -B tests/test_canvas_evidence.py
```

控制涵蓋缺片、重片、錯 head/tree/run/attempt、raw/golden 改動、zero key 遺失、計數漂移、
假 scope/summary、未擁有的實際執行、false verdict、不完整 journal、缺 producer、
數值片單一入口、原計畫順序及切點交接。原斷言、golden 各段數值、等待條件與
每片 35 分鐘 job 上限均不因收據合流而放寬。
這些純工具測試不替代真正兩片及同來源原 full 的瀏覽器驗收。

## R386：新增獨立段的固定位置與實測配片

遷移不把既有段當成可任意交換的測試：它們帶有場景、producer／consumer、教學偏好等相依，
原兩個完整區塊是不可拆的 execution units。遷移時沒有逐段 elapsed 原件，成本寫 `null`，
不以 assertion 數、平均數或猜值補齊。原每片 35 分鐘上限、各既有 wait 和 assertions 都不變。

新增模組初始固定放在第二片所有既有尾段之後、清 origin 的 `P359` 之前。需要自備場景；
`runSlotIsolation` 在每個模組外保存並還原 localStorage、sessionStorage，還原後再次逐值核對。
兩個可驗證的位置是第一片 `P88` 後、原 hand-off 檢查前，以及第二片所有既有尾段後、`P359` 前。
第一個位置之後的 `P72` 與第二個位置之後的 `P359` 都走原本自建場景的程式。
新增模組不會跳過原 hand-off、P83→P86 相依或最後的 P359。

`order.after`／`order.before` 只引用其他獨立模組，形成明確的先後約束；未知節點或循環拒絕。
有相依的模組成為同一個不可拆群組。沒有額外約束時，依 ID 的固定字元順序執行，不依檔案列舉順序。
不同 PR 新增不同 ID 的檔案，不用同時修改順序陣列、總數、projection 名單或整檔 byte pin。
若修改的是同一段既有 assertions／來源，仍須處理其實質契約衝突；本次不准用遷移改小既有計數。

### 1. 建模組，再從真 CI 取得 count 和 cost

先寫 `geometry-web/canvas_sections/Pxxxx.js`，CommonJS 預設 export 為 async 函式，接收現有 CDP helpers。
必須用現有受控 verdict 與 `=== Pxxxx.` 標頭；不得自行輸出 `CDP_RESULT`。
以傳入的 `helpers.makeCheck({prefix: 'Pxxxx ', throwOnFail: true})` 建立原框架的 assertion judge，
可直接使用 `send`、`eval_`、`waitForUI`、真 pointer／key helpers；不必另載入整個 driver。
新模組及其自帶 helper 採可靜態核對的保守子集：require／import 必須是單一字面路徑，
`.js`／`.cjs`／`.mjs`／JSON 相依整個閉包都入 module pin；不得用別名 require、module loader、
vm／eval／Function、反射 constructor 或動態 property 取得載入能力。動態陣列索引可用 `.at(i)`，
key lookup 可用 `Map.get(key)`。需要超出此子集的 helper 先擴充明確契約與反證，不默默忽略未追到的來源。
資料夾具以字面 `require('./fixture.json')` 納入閉包；新模組不提供 fs／fs.promises 的未登錄檔案讀取能力。
框架傳入的 CDP helpers 與其靜態相依、runtime／收據監督程式則共同入 slot protocol pin。

```sh
node geometry-web/canvas_registry.js stage-module --id Pxxxx
```

此工具產生 candidate 片段，`assertions: 0` 只是未驗收占位，`cost: null`、`balance: null`；
正式 `check` 必須紅。不要手填已驗收的 golden 或 cost。
執行 `Canvas section measurement` workflow，輸入該段 ID；它透過
`GEOMETRY_CANVAS_MODULE_ONLY=1`／`GEOMETRY_CANVAS_MODULE=Pxxxx` 在真瀏覽器單跑該模組。
原件記錄 head、execution SHA、tree、run／attempt、實際 exit、runtime、完整 stdout／stderr、
精確斷言數及 monotonic elapsed。這是 `capture_verified=true, acceptance=false` 的量測，不能冒充 full。

下載 GitHub 的原 artifact ZIP，再導入：

```sh
node geometry-web/canvas_registry.js import-cost --id Pxxxx --artifact-id ARTIFACT_ID --artifact ORIGINAL.zip
```

導入器即時向官方 API 核 artifact digest 與 workflow run／attempt／head，核原 ZIP、raw count、module bytes，
只修改該段片段和該段內容定址原件。正式計數由實跑寫入。之後該段可以在固定第二片位置走原 full／兩片驗收。
`GEOMETRY_CDP_UPDATE_GOLDEN=1` 現只在 TEMP 寫 full candidate 原件；既有段計數有漂移就拒絕，
不重寫封存基線，也不把 capture 當採用。

### 2. 取得兩個不可拆區塊的真成本

從一次正式 `Geometry integration` 的兩個 `canvas-shard-*` 原 artifact 分別導入：

```sh
node geometry-web/canvas_registry.js import-unit-cost --unit 1 --artifact-id ID1 --artifact ORIGINAL-1.zip
node geometry-web/canvas_registry.js import-unit-cost --unit 2 --artifact-id ID2 --artifact ORIGINAL-2.zip
```

原件必須是正式 numeric shard、完整 journal、精確 legacy census／相對次序、真 runtime 和來源身分。
沒有獨立新段的片使用原 `elapsedSeconds`；若已有新段，必須有本次 producer 的逐段 monotonic timing，
只加總原區塊的實測段耗時。不得拿新段的時間混入原區塊、用 assertion 數推估或把缺時間補零。
`units/1.json`、`units/2.json` 是獨立的校準收據；新增模組不需要改它們。重新校準是明確的證據更新。

### 3. 兩個位置都驗證後才允許自動選片

```sh
node geometry-web/canvas_registry.js propose-balance
```

工具使用兩區塊與所有新段的真成本提出有限合法配置，輸出仍是 `acceptance=false`。
執行 `Canvas slot proof` workflow，輸入該模組 ID。它在同一來源與 run／attempt 上，分別對兩個位置跑
完整模式、第一片、第二片，共六份原件；每份仍是原 35 分鐘上限。
另用真 Chromium 針對 storage 還原及還原後核對做兩個具名 `0／1／0`，不把 infrastructure error 算 killed，
不增加或改動任何既有 canvas 段計數。工具保留各自 raw、source／plan／candidate pins。

```sh
node geometry-web/canvas_registry.js import-slots --id Pxxxx --artifact-id PROOF_ID --artifact ORIGINAL-PROOF.zip
```

導入器要求六份 raw、兩個具名撤回、官方 workflow／attempt／head、當前 module 和 slot protocol bytes 全部對應，
才將這一段改成 `unit: "auto"` 並寫入它自己的 `balance` 收據。沒有兩區塊成本或任一 proof 不完整，採用拒絕。
每份證據保留原 source SHA，不會因為後來合流就改寫成新 head。

合併後，工具從全部片段重新計算配置，不提交一份每張 PR 都要改的全域 plan。
相依群組最多 24 組可選位置時，使用有界 meet-in-the-middle 求最小最大負載，最多列舉兩邊共 8192 個子集合；
超過時改用確定性 LPT，報告明寫算法，不聲稱全域最佳解。只在有證據允許的位置之間選，
預估超出原 35 分鐘上限時拒絕採用。沒有成本或位置證據時保留固定第二片，
報告 `automaticBalanceAcceptance=false`，不能聲稱自動平衡已完成。
合流後的新完整 head 仍須照常通過 full 與兩片守門；單段舊 proof 只證明其可選位置，不代替當前整體驗收。

## 原件生命週期與中斷復原

`check --verify-ci true` 對新增／變動的成本、位置收據即時核官方 artifact 及 run attempt。
總守門只從已核 PR 第一親代／main 前一版推導 `--trusted-ref <完整 SHA>`；若收據與 ZIP 的 bytes
都和可信 base Git blob 完全一致，可以繼承已採納的來源認證。每次仍重驗 raw、hash、module、count、
slot protocol 和組合的完整性，不以 JSON 自稱 trusted。這避免已採納原件因 Actions 保留期到期阻擋無關 PR。
本機未明示可信 base 時不自動信任；只有 legacy、沒有新成本時完全不觸網。

總遷移以 `tests/.registry-migration-pending` 標記寫入中的交易。此標記存在時所有 registry loader 拒絕；
請完成同一份受核遷移計畫，不能以刪標記掩蓋半套檔案。再次遷移輸出相同片段與原件，
不重抄模組原始碼，也不把目前來源內容自動改成新的 byte pin。
