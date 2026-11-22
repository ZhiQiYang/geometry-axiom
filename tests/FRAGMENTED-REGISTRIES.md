# 測試登錄片段與確定性遷移（issue #386）

新增一個套件／一個畫布段落改成新增獨立來源檔。總數、執行順序、分片與來源閉包由讀取器重算，不再提交每張 PR 都要追加的全域產生表。`公理層.md` 不變；產品原始碼本身的真正衝突仍須正常解決。

## 來源與產生結果

| 原共用位置 | 新來源 | 仍保留的守門 |
|---|---|---|
| `run_all.py` 追加名單、`run_all.expected.json` | `tests/suites.d/<套件鍵>.json` | 精確 mode/count/unit、實體檔反查、每 suite 恰好一次、原 skip 規則；既有 suite 的整份執行宣告封存在 `tests/registry-evidence/native-legacy-execution.json` 並對可信 base 的原表驗真，新 suite 由 CI 收據的 `declaration_sha256` 綁定（見下節） |
| `native_shards.py` 新來源常數、追加證據單檔 | `tests/native-costs.d/<套件鍵>.json`、`tests/registry-evidence/native/<SHA-256>.json` | 真 CI run/job/attempt/checkout、原 ZIP/report、child exit/count/seconds、來源 bytes、正式成本完整 |
| `canvas_shards.json`、`cdp_sections.golden.json` | `geometry-web/cdp_sections.d/<段 ID>.json` | 每段精確斷言數、完整且不重疊的兩片、原順序／交接、實跑 journal 與來源 |
| 每加段都改 `cdp_test.js`／共享歷史測試 | `geometry-web/canvas_sections/<段 ID>.js` 與通用 dispatcher | 每個新 module 恰有一片、每片恰有 module；歷史段仍套原逐值與順序 oracle |
| architecture source/exclusion/route 陣列 | `product-architecture.d/<集合>/<完整 path 或 identity hash>.json` | 原 Scanner 全量 inventory、互斥、K/W/H/vendor 方向、排除／vendor／route 精確 pin |

`tests/registry-layout.json` 只有固定格式版本，沒有 suite 清單、總數、最大 ID 或資料 hash。各次遷移的完整 inventory 存外部 report，不能變成下一個共享追加表。

不同新增項目使用不同識別碼。兩張 PR 若修改同一 suite、同一段或同一來源 pin，仍須合併同一份實質契約，不能透過 union merge driver 消掉。不同檔名的重複邏輯 ID、大小寫碰撞、重複 JSON key、symlink、未知欄位與不安全路徑也會被拒絕。

## 先看這裡：給要新增或修改登錄的 agent

| 你要做的事 | 走哪一節 | 一句話 |
|---|---|---|
| 新增 unittest／node --test 套件 | 「首次計數與成本」 | `--init-suite` → main 上的 `Native suite measurement` → 有權下載 artifact 的人 `--import-suite` → 採入 stage |
| 新增 python-script／node-script（只看 exit code）套件 | 同上 | `--init-suite --kind python-script|node-script`；不需要計數，仍要真 CI 成本 |
| 改既有套件的計數、needs、timeout、label | 「既有套件的執行宣告封存」 | 改片段後 `--amend-suite`；kind／cmd／files／env／mode 不准改 |
| 新增 canvas 段 | 「新 canvas 段的操作」 | 整段讀完；模組只能用受限語法 |
| 新增架構來源 | 「architecture source manifest」 | 只加 `product-architecture.d/<集合>/` 下一個片段 |
| 分支還在舊格式（有 `run_all.expected.json`） | 「首次採用與正在跑的 PR」 | 先合 main，再在合流樹上重跑 `registry_migrate.py`，不要手寫片段或 hash |

改 `run_all.py` 裡的 `PY_NEEDS`／`NODE_*` 舊表**沒有任何作用**：片段生效後那些只是遷移前的快照。漏登記時 `check_registry` 會指向 `tests/suites.d` 與 `--init-suite`。

**兩個前提，先確認再開工**
1. `Native suite measurement`（`.github/workflows/native-suite-measure.yml`）、`Canvas section measurement`（`canvas-section-measure.yml`）、`Canvas module two-slot proof`（`canvas-slot-proof.yml`）都是 `workflow_dispatch`。GitHub 只允許派發**預設分支上已存在**的 workflow 檔，所以這三支要等 #434 進 main 後才能用（派發時 ref 選你的分支）。在那之前，任何新 suite／新段都卡在量測步驟，請不要用別的 run 或手寫數字代替。
2. 導入要從 GitHub 官方 API 下載 artifact ZIP。雲端 Claude 的 egress proxy 會擋 artifact blob 主機（403），**雲端 agent 做不了這一步，也不要繞過**。請在 PR 留言請 grokbot 或本機 Claude 執行 `--import-suite`／`import-cost`，並把 stage 原樣推回分支。

## 既有套件的執行宣告封存（審查 7056059753 問題 A）

遷移前 `run_all.py` 的程式碼決定每個 suite 跑什麼；遷移後那份責任變成片段資料。若不釘住，只改資料就能把 53 項的 `py:test_serve` 改成 `python -c pass`、`exit-code-only`，所有守門仍綠。現在有三層：

1. **封存目錄** `tests/registry-evidence/native-legacy-execution.json`：每個遷移前 suite 的完整宣告（`order`、`execution` 全欄、`files`、`expected`），不可追加。`load_registry` 對每個既有名稱要求片段宣告逐值相等（`R386_NATIVE_LEGACY_EXECUTION_PIN`）；不在目錄裡的 suite 必須是 `new/` order；目錄裡的 suite 不准消失。
2. **對可信 base 驗真**（`verify_legacy_execution`，registry contract 與 `--verify-ci` 都會跑）：
   - base 已有這個檔：Git bytes 必須相同（`..._CATALOG_IS_IMMUTABLE`）。
   - base 尚未遷移（第一次採用，例如 #434 對 main）：從 base 的 Git 物件抽出 `tests/` 頂層與宣告提到的檔，執行 base **自己的** `build_suites()`／`load_expected()`，用遷移工具同一個正規化函式重新推導，必須逐值相等（`..._NOT_IN_TRUSTED_BASE`）。抽出不足只會推導出不同結果而紅，不會放行。
3. **結構綁定**（所有 suite，含新 suite）：`py:` ⇔ `unittest`；`node:` ⇔ `node-*` 且 `needs_node`；`python-script` 的 cmd 開頭必須是 `{python} {root}/<files[0]>`；`node-script`／`node-canvas` 的 `cmd[0]` 必須是 `files[0]`；`mutation:check` 的 cmd 固定（`R386_NATIVE_EXECUTION_FILE_BINDING`）。

新 suite 不進封存目錄；它的 `name`／`execution`／`files` 由 CI 收據的 `suite_binding.declaration_sha256` 綁定，改了就 `R386_NATIVE_STALE_SUITE_SOURCE_OR_EXECUTION`，必須重新量測。

**合法改動既有 suite：具名修訂。** 例如 #437 把 `py:test_gdi_contract` 從 5 項改成 10 項，並增加 needs：

```bash
# 1. 直接改片段（count、needs），再寫修訂；before 雜湊由工具從封存目錄算
python3 -B tests/native_registry.py --amend-suite py:test_gdi_contract \
  --reason "#437 World 堆疊：test_gdi_contract 新增 5 項並需要 core／bridge／model-base"
# 2. 實跑確認新計數（計數仍由每次實跑核對，修訂不能憑空設數字）
python3 -B tests/run_all.py --build --only py:test_gdi_contract
```

修訂寫在 `tests/registry-evidence/native-amendments/<套件鍵>.json`，一個 suite 一檔（同一 suite 被兩張 PR 修訂就是真衝突，要正常合流）。只准改 `expected.count`、**增加** `needs`、`timeout`、`label`；改 kind、cmd、files、extra_env、needs_node、order、mode、unit 一律 `R386_NATIVE_AMENDMENT_FIELD`。要換執行方式就新增一個新 suite。目前不支援退休既有 suite；真的需要時要擴充這個具名修訂流程並另外審查。

## native 六片

遷移讀當前 checkout 的真 `build_suites()` 與 expected，不把開工時的名單硬寫進工具。舊 suite 保留原執行順序，新增 suite 按穩定識別碼排序。六片繼續用原多情境、有界交換規劃器；完整四輪觀測保留為四個不同情境，不平均掉慢 runner，片內仍保留 runner 原順序。

開工基底的 `native_shard_timings.json` 和三份追加證據保留原路徑，原 bytes 另存內容定址來源。工具也辨識後續已採納的 `native_shard_added_receipts.json` v1，沿用其原 count-mode／exit／來源／margin 條件；不是把來源數固定成四個。新增 suite 不再改這些歷史檔或 loader 常數。歷史 scalar 三片重播的預設權重只屬原歷史測法；正式六片遇到未量測 suite 必須拒絕，不能用 1000 ms 補值。

main #438（R03）新增的 `native_shard_added_evidence_r03.json` 是另一種歷史來源：`native-shard-workspace-suite-evidence/2`，明寫 `kind: workspace`，不是 GitHub CI 收據。遷移時它歸為 `historical-workspace`：頂層 JSON 照樣原 bytes 內容定址存進 `registry-evidence/native/`；它指名的 stdout／receipt／child 原件留在 `tests/native_shard_evidence/` 原位，每次讀 registry 都複製到隔離目錄，交給 main 原封不動的 `native_shard_workspace.load()` 全量驗（來源 pin、binary 指紋、row、餘裕）。可信 base 推導時原件取自 base 的 Git 物件。這只是承認已採納的歷史來源，新 suite 仍走真 CI。

首次遷移另產生不可追加的 `tests/registry-evidence/native-legacy.json`，其來源逐 byte 對明示 base 的 Git 原件核實。只有該 catalog 原本具名的套件可使用 historical 成本類型；新 suite 必須走真 CI，不能自行新增一份看似歷史 JSON 規避來源驗真。

原 `node:tests-js` 是整體計數的既存 suite，沒有每檔真原件就不能虛構個別 count/cost。新 JS 檔宣告成自己的 node suite，不再追加既有 aggregate 名單。

### 首次計數與成本

1. **寫測試檔，產生候選宣告。** 新 ID 不可覆寫既有宣告；必要 binary 用 `--needs` 逐一列（可重複）。
   ```bash
   # 有計數的套件（unittest：名稱必須是 py:<檔名主幹>；node --test：名稱 node:<任意>）
   python3 -B tests/native_registry.py --init-suite py:test_example --kind unittest --file tests/test_example.py --needs bridge
   python3 -B tests/native_registry.py --init-suite node:example --kind node-test --file tests/test_example.js
   # 只看 exit code 的套件（名稱不可用 py:；node-script 用 node:）
   python3 -B tests/native_registry.py --init-suite script:example --kind python-script --file tests/example_check.py
   python3 -B tests/native_registry.py --init-suite node:example_script --kind node-script --file tests/example_script.js
   ```
   unittest／node-test 的 expected 是 `pending-ci-census`；python-script／node-script 直接是 `exit-code-only`，cmd 由工具固定成「執行該檔」，不能自行加別的指令。
2. **本機只能量測，不能驗收。** `python3 -B tests/run_all.py --build --measure-suite EXACT_NAME --report OUT.json` 能讀 pending；正式 runner、六片、complete 都拒絕 pending 與沒有成本的 suite（`R386_NATIVE_EXACT_EXPECTED`／`R386_NATIVE_EXACT_COST_COVERAGE`）。
3. **在 CI 真量測。** 推送分支後，派發 `Native suite measurement`，ref 選你的分支，`suite` 填完整名稱。需要 #434 已在 main（見上方前提 1）。artifact 名稱是 `native-suite-measurement`，ZIP 內的 report 成員是 `report.json`。report 是 `acceptance=false`，不是六片全過。
4. **導入（由 grokbot 或本機 Claude 做，見上方前提 2）。** 四個 ID 從該 run 取得：run id、量測 job id、artifact id；`--planning-upper-ms` 必須嚴格大於 report 裡的實測毫秒且小於 1200000，是規劃上界，不是實測。`--out` 必須是 checkout 外的新空目錄。
   ```bash
   GH_TOKEN=... python3 -B tests/native_registry.py --import-suite py:test_example \
     --run-id RUN_ID --job-id JOB_ID --artifact-id ARTIFACT_ID \
     --member report.json --planning-upper-ms 30000 --out /tmp/native-import-stage
   ```
   工具只寫 stage，不改 repo。輸出列出 stage 內的檔：
   - `tests/registry-evidence/native/<SHA-256>.json`：原 API JSON＋原 ZIP（內容定址）
   - `tests/native-costs.d/<套件鍵>.json`：成本指標
   - 只有 pending 時：`tests/suites.d/<套件鍵>.json`，expected 換成原件的真計數
5. **採入 stage。** 原樣複製進 checkout（`cp -R /tmp/native-import-stage/tests/. tests/`），不要手改任何一個 byte，再跑 `python3 -B tests/registry_migrate.py check --trusted-base <main 完整 SHA> --self-test` 與 `python3 -B tests/run_all.py --build --only <名稱>`，推送後等正式六片與 complete。既有 expected 不被首次計數工具修改。

新成本逐次綁目前 suite script 與 execution；同名、同 count、不同測試不能借舊成本。只釘必要的套件自身來源，不把每個產品變動當作全部成本失效。原四份歷史資料保留原本跨 head 的觀察規則。每片仍須嚴格小於 1200 秒，所有原 job／child 時限保持。

### 原件到期與可信基底

新成本／proof 要在線核官方 artifact 身分及 digest；自填 API JSON 和自行計算的 ZIP hash 不能自證來源。已在可信 main 基底的內容定址原件，以該基底相同 Git blob 承繼來源驗真，仍重驗內部來源、count、cost、bytes。Actions 保留期結束不會讓整個 repo 永久失效。

CI 的信任錨點來自事件及真正 checkout：PR 要先核 `HEAD^2` 等於事件 head，再用 `HEAD^1`；main push 用第一親代。不得採用 PR receipt 自填的 base。其他事件與一般本機預設不承繼；本機顯式 `--trusted-base <完整 SHA>` 在 report 標明為呼叫者指定。

## canvas 兩片、成本與歷史 pin

既有 canvas 序列有狀態，不能任意用 LPT 重排每段。開工版只有 P88 → P72 一個已驗證的交接點，且舊原件沒有逐段 CI 耗時。遷移完整保留兩個既有執行單位、切點、storage handoff、尾序與 adjacency。未知成本是 null，不以斷言數或本機速度換算。

原 plan/golden bytes 與來源 SHA 存於 `geometry-web/canvas-registry/legacy.*`。歷史測試取得目前片段組合結果的 legacy projection，再套原 91 段／4002 斷言與後續各層精確 oracle，不能直接把封存 fixture 當 actual。新段由通用 module/count/owner/source/receipt 守門驗，不必每 PR 再加一層共享投影。

新段使用獨立 module、精確 count、顯式順序依賴與真 CI 量測。總數相加、拓樸同分按段 ID 決定；缺依賴或循環必紅。同一來源集合不因加入次序改變 plan 或 hash。

成本平衡只在有狀態隔離證明的 slot 中選。預設入口在全部既有尾段之後、P359 之前，不越過後續基底已加入的 P420／P1161 等段；另一入口在 P88 後、原 handoff 驗證前。每個 module 的 wrapper 保存／恢復兩種 storage 並驗證，module 須自備 fixture。要成為 `unit:auto`，需其兩 slot × full／shard1／shard2 的真原件及 wrapper 具名撤回，不能用「有計時」代替「可安全移動」。兩個 opaque unit 的時間也必須來自正式收據；齊備後 planner 依實測成本、依賴和合法 slot 決定分配。

候選量測、slot proof 與調配都不冒稱正式 acceptance。採入後仍需目前合併全集的兩片原件與完整來源閉包。瀏覽器程式碼、回歸和 CI 收集器隨補丁提供，由可開 Chromium 的 CI 實跑。本片支援新增獨立段，既有段內容仍受原 assertions／來源守門約束；既有段 count 的合法變更需要另行審查的具名契約遷移。一般 capture 不能改寫歷史封存或抹掉舊 pin，遷移也不能在缺封存時回頭重建它。

### 新 canvas 段的操作

**開工前把本節整段讀完。** 兩個常見卡點：
- `geometry-web/canvas_sections/` 目錄目前不存在，第一位新增者自己建立；目錄已在 `.gitattributes` 設成 LF。
- 模組只能用受限語法子集（本節最後一段）：不能用 `fs`、動態 `require`、`eval`／`Function`／`vm`、`module`／`createRequire`、反射 constructor、動態 computed property。違反時 `stage-module` 或 check 會拒絕，不是 bug。
- 三支 workflow 要等 #434 進 main 後才能派發；下載原 ZIP（`--artifact ORIGINAL.zip`）同樣由 grokbot 或本機 Claude 做（見本文開頭前提）。

先寫 `geometry-web/canvas_sections/P999.js`，再產生候選宣告：

```bash
node geometry-web/canvas_registry.js stage-module --id P999
# 真有新模組間的順序相依才加 --after P998 或 --before P1000。
```

候選的零 count 不是正式 golden；正式 check 必拒絕。執行 `Canvas section measurement` workflow 的 section=`P999`，下載官方原 ZIP，再導入它的真 count／cost：

```bash
node geometry-web/canvas_registry.js import-cost --id P999 --artifact-id ID --artifact ORIGINAL.zip
```

此時模組固定在第二片的尾 slot。要允許依實測成本移動，先從正式 `Geometry integration` 兩片原 ZIP 導入各 unit 的時間，再執行 `Canvas module two-slot proof`（`canvas-slot-proof.yml`）的六次真 capture 與兩項具名撤回：

```bash
node geometry-web/canvas_registry.js import-unit-cost --unit 1 --artifact-id ID1 --artifact ORIGINAL-1.zip
node geometry-web/canvas_registry.js import-unit-cost --unit 2 --artifact-id ID2 --artifact ORIGINAL-2.zip
node geometry-web/canvas_registry.js import-slots --id P999 --artifact-id PROOF_ID --artifact ORIGINAL-PROOF.zip
node geometry-web/canvas_registry.js propose-balance
```

導入工具核官方 artifact digest、workflow/run/attempt/head 以及原件的 source／count／timing；候選與 proof 都是 `acceptance=false`。超過原 35 分鐘預算不准採用。最多 24 個可動相依群組使用有界精確平衡；更多群組用確定性 LPT，報告不聲稱全域最優。

模組匯出 `async helpers => { ... }`，使用既有 CDP helpers、`makeCheck()` 與自己的 fixture。它的 literal require/import（含轉遞 `.js/.cjs/.mjs/.json`）全部入來源閉包；動態或別名 loader、`module/createRequire`、`eval/Function/vm`、反射 constructor、動態 computed property、`fs/fs.promises` 不在可採用子集。JSON fixture 用 literal `require('./fixture.json')`；動態陣列索引用 `.at(i)`、map 用 `.get(key)`。這個保守限制讓被執行的來源可完整釘選；需要擴展語法時應連同閉包解析守門審查，不能用宣告繞過。

## 獨立 CDP driver 段（`execution.kind: "driver"`，#445）

有些驗收段需要 module 子集不准的能力：讀寫實檔、解 ZIP、另開原生服務與新的 Chrome 進程。例如 P2052（R03 固定治具）的冷開 6 項。這類段不改寫成 module，改登錄成 **driver**：原 driver 檔一字不動，由 `cdp_test.js` 的固定一句派發，`module` 的 strict 限制一個字都不放寬。裁定見 ChatGPT 7070056758（四項硬條件），加嚴見 7072803590。

### 誰能新增

driver 只能是 `geometry-web/canvas_registry.js` 裡寫死的 `DRIVER_SECTIONS` 封閉清單上的一筆（目前只有 `P2052`）。片段 JSON 只能逐值重述清單內容，寫別的檔名、flag、unit、錨點、多一個鍵，都會 `R386_CANVAS_DRIVER_UNREVIEWED`。

**信任層級（對抗審查 7072484935 X1，#434 既有，本 PR 不修，只如實記載）**：清單和檢查它的程式都在 `canvas_registry.js`，而這支檔 PR 可以改。所謂「重審」，只是用工具把 `tests/registry-source-reviews/` 和架構排除 pin 的雜湊重算一遍，沒有對可信 base 鎖定。所以真正的防線是**人審 `canvas_registry.js` 的 diff**。同理，量測 workflow 與 `.github/scripts/canvas_section_measure.py` 跑的是分支上的版本（X2）。

### 新增或修改的步驟

1. 寫 driver 檔，並在 `cdp_test.js` 加 SCOPE flag、外層 guard 與一句派發。派發的位置、前一句、後一句都要固定。
2. 在 `DRIVER_SECTIONS` 加一筆。要寫的欄位：
   - `driver`、`flag`、`unit`、`after`／`before`；
   - 28 類的具名斷言名單；
   - `dispatch`：派發區塊原文；`following`：派發後的下一句原文；`guard`；
   - `closure`：依賴閉包的檔案集合；`builtins`、`vendor`、`processProperties`；
   - `computed`：已審的動態成員位置；
   - `subprocess`：唯一的 child_process import、可呼叫的名稱、每個呼叫點，以及被執行的腳本；
   - `outputs`：driver 會寫出的檔。
   `computed` 和 `subprocess.sites` 的每一項寫成「原文@所在最內層函式的 LF SHA-256」。閉包內的檔改動到這些函式，就要重算並重審。
3. `node geometry-web/canvas_registry.js stage-driver --id <ID>` 產生候選（assertions 0、cost null）。這時正式 check 會拒絕，canvas 兩片會紅，這是預期的。
4. 推送後，派發 `Canvas section measurement`，section 填 `<ID>`，ref 選分支。
5. 由 grokbot 或本機 Claude 執行 `node geometry-web/canvas_registry.js import-cost --id <ID> --artifact-id ID --artifact ORIGINAL.zip`，並採入（雲端 agent 下載不了 artifact，見本文開頭前提 2）。
6. 新 head 觸發 Mutation evidence 並採入，再跑正式 CI。

改閉包內任何檔、被執行的腳本、`cdp_test.js` 的派發區塊或清單本身，`driverIdentity` 都會變，舊收據就以 `R386_CANVAS_COST_SOURCE` 失效，要從第 4 步重做。`node geometry-web/canvas_registry.js driver-identity --id <ID>` 可以先看閉包守門是否通過。

### 靜態守門驗什麼

**閉包**（`driverClosure`，`R386_CANVAS_DRIVER_CLOSURE_*`／`_SUBPROCESS`／`_PROCESS_CAPABILITY`）：

- `require`／`import` 只准字面，而且只能直接呼叫。
- 禁用 `eval`／`Function`／`Reflect`／`Proxy`／`globalThis` 等名稱，名稱當成員或字串常量也一樣禁。
- 禁止成員 `constructor`／`__proto__`／`getPrototypeOf`／`getOwnPropertyDescriptor` 等反射路徑，包括解構取用（`{constructor:F}=fn`）。
- 計算屬性和 module strict 一樣只准字面，例外是 `computed` 清單上的已審位置，清單必須逐一相等。
- `process` 只准 `env`（唯讀）、`kill`、`platform`。
- child_process 只能經那一句已審 import 取得，每個 `spawn`／`spawnSync`／`ownedSpawn` 呼叫點都要在 `subprocess.sites` 上，集合必須逐一相等。
- 閉包的實際檔案集合必須等於清單。vendor 葉節點只把 bytes 納入 hash，不審它的語法。

**派發**（`driverDispatch`，`R386_CANVAS_DRIVER_DISPATCH`）：

- 用 AST 解析 `cdp_test.js`。所有 `require()`／`import()` 的模組路徑先正規化，引號、副檔名不拘，指向 driver 的必須恰好一次；字串常量中出現 driver 名稱的也必須恰好一次。
- 派發句必須是已審 `if` 的唯一結果。前一句是 guard 區塊（最後一句是 P205），後一句是 `following`。
- 片段順序另由 `_ANCHOR`／`_OWNER`／`_ORDER`／`R386_CANVAS_TERMINAL_SLOT` 擋。

**來源身分**（`driverIdentity`）包含：

- 閉包逐檔 LF sha256；
- `subprocess.scripts`，也就是被執行的 `serve.py`、`start_local.py`、`tests/binaries.py` 的 LF sha256；
- 派發區塊 sha256；
- 清單條目本身。

### 收據（`geometry-canvas-driver-measurement/2`）驗什麼

- ZIP 的檔案集合、每檔 hash。
- 唯一一行 CDP_RESULT：partial 模式、0 失敗、`sectionOrder==[ID]`、計數等於清單長度。
- 28 個具名 `✓` 各恰好一次，沒有 `✗`。
- **F1**：
  - `sourceService` 逐值等於量測腳本自己的 `runtime.stdout` 探測。
  - 冷開服務的 `version`／`root` 等於量測版本與 root。
  - 冷開服務（argv 是 `serve.py <port>`）與冷開 Chrome（argv 含 `--user-data-dir=<profile>`）必須出現在量測腳本自己取樣 `/proc` 的 `process-ledger.json` 中，並且是 `cdp_test.js` 的子孫；來源服務不得是它的子孫。
- **F2**：`CDP_SCOPE` 恰好一行，且等於結果的 scope。段標題 < 具名檢查 < SCOPE 行 < CDP_RESULT，PACKAGE 行在段內。
- **F3**：兩份竄改檔是合法 ZIP，`world.scene` 與存檔相同，manifest 恰好是存檔加上 driver 的那一處修改。
- **F4**：存檔是合法 `.gcanvas`：只含 `manifest.json`＋`world.scene`，`format`、`sceneHash` 正確，恰有一份 v2 配方，至少有一份 v1 配方。

### 不驗什麼（如實記載）

- **進程帳不依賴 driver，但依賴量測腳本。** 量測腳本由分支提供（X2），手寫 ZIP 過不了 `import-cost` 的在線 digest，但改了腳本的官方 artifact 過得了。最後一道是正式 canvas 第 2 片的真執行與逐段計數。
- **「竄改檔被產品拒收」這一層只看 driver 自己印的 `WRONG_V2_POLICY`／`UNKNOWN_VERSION ✓`。** 收據驗的是竄改內容確實如預期，不驗瀏覽器裡的拒收行為本身。
- **log 是否完整無刪，收據層無法獨立驗。** F2 只驗結構與順序。
- **間接依賴只在量測當時涵蓋。** `serve.py` 間接 import 的 `geometry-web/*.py`、bridge 來源由 runtime 指紋（`runtime_version.py::source_version`，含 `geometry-web`、`geometry-core` 等目錄的 `.py`／`.c`／`.h`／`.inc`）涵蓋：量測當時冷開服務的 `version` 必須等於該指紋，量測腳本收尾時再重算一次。但這不進 `driverIdentity`，所以這些檔之後改了，舊收據不會失效。Chrome 執行檔、Python 直譯器、`taskkill` 是外部程式，不在 hash 內。
- **執行期寫檔不擋。** driver 執行時用 `fs` 改寫再還原 repo 檔，靜態守門擋不住；量測腳本收尾的 `driver_identity()` 與 `source_identity()` 只擋「改了沒還原」。
- **`cdp_test.js` 本體不在 hash 內**（X4，#434 既有）：派發區塊以外的部分不進 `driver_sha256`。module 也是一樣。
- **module strict 的既有缺口**（X3，#434 既有）：module strict closure 目前仍接受解構取 `constructor`。本 PR 沒有改 module strict。`R386_CANVAS_STRICT_MODULE_SOURCE_PINNED` 把 module strict 路徑 8 個函式的原文釘在 main `883e6868`，要補這個缺口必須另開審查。

## 行尾（審查 7056059753 問題 B）

讀取端拒絕 CR，因為片段 bytes 直接進 `source_digest`、成本綁定與來源閉包。Windows 的 `core.autocrlf` 會把沒有標記的檔簽出成 CRLF（`公理層.md` 就是這樣），所以 `.gitattributes` 把作者編寫的片段目錄設成 `text eol=lf`（`tests/suites.d/**`、`tests/native-costs.d/**`、`tests/registry-layout.json`、`tests/registry-evidence/*.json`、`native-amendments/**`、`tests/registry-source-reviews/**`、`geometry-web/cdp_sections.d/**`、`geometry-web/canvas_sections/**`、`product-architecture.json` 與 `.d/**`），內容定址原件（`tests/registry-evidence/native/**`、`geometry-web/canvas-registry/**`）設成 `-text`，逐 byte 不轉換。若本機仍看到 `R386_NATIVE_PURE_LF`，先查 `git check-attr text eol -- <檔>`，不要放寬讀取端。

## architecture source manifest

根檔只保留 schema、roots、searchRoots、policy。來源／排除各按完整 path 一片，route／trusted bundle 按完整 identity 一片。展開後交給原 Scanner，不改掃描責任、不加 directory exemption。

`manifest_input_bytes()` 綁根檔及全部排序後片段的路徑、長度與 LF bytes 雜湊；`manifest_input_paths()` 提供 tracked-clean 閉包。scanner hash 同時包含新讀取器。只改 layer、purpose、route、排除 pin 也會改輸入閉包。

本片新增 driver 與改接測試入口需要一次精確登錄。`tests/registry-source-reviews/` 是工具計算的逐檔 before／after 審查紀錄，只允許本片四個具名 driver：當前 bytes 等於已審 after、原登錄等於已審 before 才更新，其餘來源 pin 不動。它不是 refresh-all-hashes。未來合法合流若改同一 driver，要重審該來源，不能套本片舊 pin。

## 遷移與回復

完整 SHA 是本次輸入身分，工具沒有只接受開工 SHA 的特判。它從當前合法格式讀所有項目，遇未知 schema、缺證據或歧義停止，不猜補。再執行已遷移來源會保留相同 payload bytes。

```bash
python3 -B tests/registry_migrate.py plan --base-sha FULL_SHA --out /tmp/registry-plan --report /tmp/registry-plan.json
python3 -B tests/registry_migrate.py apply --base-sha FULL_SHA --report /tmp/registry-apply.json
python3 -B tests/registry_migrate.py check --trusted-base FULL_MAIN_SHA --self-test --report /tmp/registry-check.json
```

`--out` 必須是 checkout 外的新目錄。`files/` 是產生結果；`manifest.json` 列完整 base、每個 input/output 的 bytes／SHA-256／Git blob、before／after。不含時間戳、絕對路徑或隨機值，也沒有每新增一片必改的 tracked inventory。

上面的 `--trusted-base` 是本機明示已核實 main；CI 不接收這個參數，會自事件推導可信 parent。初次本機 apply 以明示的 migration input base 核既有歷史來源，report 會標示這個信任來源。

apply 先在完整來源副本覆蓋候選並驗原守門，再核來源未變才寫入。寫入前保留 journal／備份；正常錯誤回復。多檔寫入不是單一檔案系統交易，若程序中斷，consumer 拒未完成狀態，用 `registry_migrate.py recover` 回復。後續有人改檔時 recover 拒絕覆蓋。準備期中斷尚未寫來源，可安全清掉未完成備份。

遷移退休 `run_all.expected.json`、`canvas_shards.json`、`cdp_sections.golden.json`，所有實際 consumer 改讀聚合 API。歷史原件、scalar replay 和舊 hash 比對保留，衍生結果不手寫。

## CI、path scope、相關補丁

- native 仍六片、max-parallel 6、各 35 分鐘；原 receipt verifier 檢完整互斥。新基礎設施契約測試是 workflow 明確跑、記錄計數/log 的獨立 gate，不冒充有成本的新 native suite。
- `registry-contract` 在自己的 5 分鐘 job 執行完整 `check --self-test`，以 Node 24、兩層 Git 歷史與原 sparse 排除讀取來源，保存原 `registry-contract.json`。`native-complete` 的原反證、archive 與六片收據核對仍共用原 5 分鐘；它等待 native 和 registry 兩邊，並明確要求 registry 結果為 success，因此 `always()` 不會把失敗、取消或略過的新 gate 隱藏成綠燈。新 job 不占用原 coverage 的驗證預算，也不改六片或八組 browser 排程。
- canvas 仍兩片，原八組 browser、各 job 時限、complete 5 分鐘、child 60 秒及既有 assertions 不變。新收集 workflow 只取真量測，不取代完整驗收。
- 純 native suite/cost/原件仍只需 native；canvas module／片段／原件、共同 layout/migrator 與 architecture 來源片段觸發完整 browser 路徑。未知、刪除、分類失敗、main push 保持原保守規則。
- 11/15 issue #386 四路 browser／native 單次建置補丁負責排程及 binary 傳遞，本片負責 registry。`build_suites()`、`load_expected()` 預設介面保留，build producer 的 needs 聯集仍從真 registry 取。兩份文字補丁需一次 `run_all.py`／workflow 接線合流，不能稱任意套用順序零衝突。本片不另改四路排程或 binary archive 協定。
- #214／#418 的 mutation ledger 與三份 architecture 衍生物不在本片，沒有改動。#418 原 reader 只釘 root manifest 和舊 generator，不能直接驗新格式。若它先合，該機制須先加片段閉包／generator 版本 adapter，再於新乾淨 head 產真正新原件，凍結原件和舊 pin 保留。本工具對尚未宣告此格式協定的 reader 拒絕，不偷換 frozen pin。

## 首次採用與正在跑的 PR

選一次共同切換點。若 #427 已先合併，在新的 main 重跑工具，不能套舊 inventory。切換時只暫停登錄來源採入，產品分支仍可開發；工具、守門、工具生成的當前片段在同一次正式採入，保存完整 SHA/report/hash。

**同一個既有 suite 在兩邊都改了（例：#437 的 `py:test_gdi_contract` 5→10 與 needs）**
- 舊格式那邊先進 main：本 PR 這類遷移分支合 main 時，要回到「main＋遷移工具、尚未遷移」的合流樹重跑 `plan/apply/check`，封存目錄會直接記到新值，不需要修訂；`check` 會對新 main 的原表重新推導驗真。
- 遷移先進 main：舊格式 PR 合 main 時，`run_all.expected.json` 已被刪、`PY_NEEDS` 已無作用。把計數與 needs 改寫進 `tests/suites.d/<鍵>.json`，再 `--amend-suite`。只改 `run_all.py` 會讓 needs 默默留在舊值，`run_all.py --only` 的實跑計數也會紅。

尚未合併的 PR 各適配一次：保留本 PR 真正新增的測試，把 suite/段落/架構路徑轉成其自己的片段；去掉對退休表和共享投影的機械追加，不能丟產品修改、舊斷言、原 CI 證據。缺新格式來源綁定時只補該 suite/module 真量測。之後不同新增項目可直接合流，合併全集仍跑 CI。

這消除登錄表引起的反覆合流，不保證所有產品 PR 免重測。產品來源、執行器、成本或 assertion 真正變動時仍要更新證據；不可變原件重用沿 #214／#418，不能為省突變時間放寬來源適用範圍。
