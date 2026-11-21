# 測試登錄片段與確定性遷移（issue #386）

新增一個套件／一個畫布段落改成新增獨立來源檔。總數、執行順序、分片與來源閉包由讀取器重算，不再提交每張 PR 都要追加的全域產生表。`公理層.md` 不變；產品原始碼本身的真正衝突仍須正常解決。

## 來源與產生結果

| 原共用位置 | 新來源 | 仍保留的守門 |
|---|---|---|
| `run_all.py` 追加名單、`run_all.expected.json` | `tests/suites.d/<套件鍵>.json` | 執行宣告、精確 mode/count/unit、實體檔反查、每 suite 恰好一次、原 skip 規則 |
| `native_shards.py` 新來源常數、追加證據單檔 | `tests/native-costs.d/<套件鍵>.json`、`tests/registry-evidence/native/<SHA-256>.json` | 真 CI run/job/attempt/checkout、原 ZIP/report、child exit/count/seconds、來源 bytes、正式成本完整 |
| `canvas_shards.json`、`cdp_sections.golden.json` | `geometry-web/cdp_sections.d/<段 ID>.json` | 每段精確斷言數、完整且不重疊的兩片、原順序／交接、實跑 journal 與來源 |
| 每加段都改 `cdp_test.js`／共享歷史測試 | `geometry-web/canvas_sections/<段 ID>.js` 與通用 dispatcher | 每個新 module 恰有一片、每片恰有 module；歷史段仍套原逐值與順序 oracle |
| architecture source/exclusion/route 陣列 | `product-architecture.d/<集合>/<完整 path 或 identity hash>.json` | 原 Scanner 全量 inventory、互斥、K/W/H/vendor 方向、排除／vendor／route 精確 pin |

`tests/registry-layout.json` 只有固定格式版本，沒有 suite 清單、總數、最大 ID 或資料 hash。各次遷移的完整 inventory 存外部 report，不能變成下一個共享追加表。

不同新增項目使用不同識別碼。兩張 PR 若修改同一 suite、同一段或同一來源 pin，仍須合併同一份實質契約，不能透過 union merge driver 消掉。不同檔名的重複邏輯 ID、大小寫碰撞、重複 JSON key、symlink、未知欄位與不安全路徑也會被拒絕。

## native 六片

遷移讀當前 checkout 的真 `build_suites()` 與 expected，不把開工時的名單硬寫進工具。舊 suite 保留原執行順序，新增 suite 按穩定識別碼排序。六片繼續用原多情境、有界交換規劃器；完整四輪觀測保留為四個不同情境，不平均掉慢 runner，片內仍保留 runner 原順序。

開工基底的 `native_shard_timings.json` 和三份追加證據保留原路徑，原 bytes 另存內容定址來源。工具也辨識後續已採納的 `native_shard_added_receipts.json` v1，沿用其原 count-mode／exit／來源／margin 條件；不是把來源數固定成四個。新增 suite 不再改這些歷史檔或 loader 常數。歷史 scalar 三片重播的預設權重只屬原歷史測法；正式六片遇到未量測 suite 必須拒絕，不能用 1000 ms 補值。

首次遷移另產生不可追加的 `tests/registry-evidence/native-legacy.json`，其來源逐 byte 對明示 base 的 Git 原件核實。只有該 catalog 原本具名的套件可使用 historical 成本類型；新 suite 必須走真 CI，不能自行新增一份看似歷史 JSON 規避來源驗真。

原 `node:tests-js` 是整體計數的既存 suite，沒有每檔真原件就不能虛構個別 count/cost。新 JS 檔宣告成自己的 node suite，不再追加既有 aggregate 名單。

### 首次計數與成本

1. 新增測試原始檔，用 `native_registry.py --init-suite` 產生候選宣告。例如 `--init-suite py:test_example --kind unittest --file tests/test_example.py`，必要 binary 以 `--needs` 明列。新 ID 不可覆寫既有宣告。
2. 首次 expected 是 `pending-ci-census`。只有 `run_all.py --build --measure-suite EXACT_NAME --report OUT` 能讀它；正式 runner／六片／完整守門都拒絕 pending。
3. `Native suite measurement` workflow 在候選 ref 真跑同一 suite，保留原 assertions、timeout、實際 exit/count/seconds、測試 script／execution 宣告與 CI 身分；report 為 `acceptance=false`，不是六片全過。
4. `native_registry.py --import-suite NAME --run-id RUN --job-id JOB --artifact-id ARTIFACT --member report.json --planning-upper-ms UPPER --out STAGE` 下載官方 API 與原 ZIP。只有新 suite 的原成功計數能填入片段；上界必須嚴格大於原實測毫秒，不能把上界稱為實測。
5. 採入 stage 中該 suite 的宣告、成本與原件，再跑正式六片及 complete。既有 expected 不被首次計數工具修改。

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

先寫 `geometry-web/canvas_sections/P999.js`，再產生候選宣告：

```bash
node geometry-web/canvas_registry.js stage-module --id P999
# 真有新模組間的順序相依才加 --after P998 或 --before P1000。
```

候選的零 count 不是正式 golden；正式 check 必拒絕。執行 `Canvas section measurement` workflow 的 section=`P999`，下載官方原 ZIP，再導入它的真 count／cost：

```bash
node geometry-web/canvas_registry.js import-cost --id P999 --artifact-id ID --artifact ORIGINAL.zip
```

此時模組固定在第二片的尾 slot。要允許依實測成本移動，先從正式 `Geometry integration` 兩片原 ZIP 導入各 unit 的時間，再執行 `Canvas slot proof` 的六次真 capture 與兩項具名撤回：

```bash
node geometry-web/canvas_registry.js import-unit-cost --unit 1 --artifact-id ID1 --artifact ORIGINAL-1.zip
node geometry-web/canvas_registry.js import-unit-cost --unit 2 --artifact-id ID2 --artifact ORIGINAL-2.zip
node geometry-web/canvas_registry.js import-slots --id P999 --artifact-id PROOF_ID --artifact ORIGINAL-PROOF.zip
node geometry-web/canvas_registry.js propose-balance
```

導入工具核官方 artifact digest、workflow/run/attempt/head 以及原件的 source／count／timing；候選與 proof 都是 `acceptance=false`。超過原 35 分鐘預算不准採用。最多 24 個可動相依群組使用有界精確平衡；更多群組用確定性 LPT，報告不聲稱全域最優。

模組匯出 `async helpers => { ... }`，使用既有 CDP helpers、`makeCheck()` 與自己的 fixture。它的 literal require/import（含轉遞 `.js/.cjs/.mjs/.json`）全部入來源閉包；動態或別名 loader、`module/createRequire`、`eval/Function/vm`、反射 constructor、動態 computed property、`fs/fs.promises` 不在可採用子集。JSON fixture 用 literal `require('./fixture.json')`；動態陣列索引用 `.at(i)`、map 用 `.get(key)`。這個保守限制讓被執行的來源可完整釘選；需要擴展語法時應連同閉包解析守門審查，不能用宣告繞過。

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

尚未合併的 PR 各適配一次：保留本 PR 真正新增的測試，把 suite/段落/架構路徑轉成其自己的片段；去掉對退休表和共享投影的機械追加，不能丟產品修改、舊斷言、原 CI 證據。缺新格式來源綁定時只補該 suite/module 真量測。之後不同新增項目可直接合流，合併全集仍跑 CI。

這消除登錄表引起的反覆合流，不保證所有產品 PR 免重測。產品來源、執行器、成本或 assertion 真正變動時仍要更新證據；不可變原件重用沿 #214／#418，不能為省突變時間放寬來源適用範圍。
