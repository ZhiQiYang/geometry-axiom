# R16／U123-H:A：P1231 登錄與雲端實跑交接

本片固定基底 `1b1c66749786c238042e3ba1c3917b1ad33b31bc`。開工時 PR #434
尚未合併，因此 T→P 按現行單檔格式交付。產品高度契約見 `DOM-CONTRACT.md`；
本文件只說明新增測試的歸屬、golden 與片段格式的接續，不宣稱瀏覽器已通過。

## 本片的獨立段落

- 段 ID 是 **P1231**。`P123H` 會被現行 `cdp_floor.sectionOf()` 歸成 P123；
  使用數字段即可保留原標頭解析規則。
- 實作在 `geometry-web/workspace_height_test.js`，只使用傳入的 CDP helpers。
  `makeCheck` 由 driver 提供，避免把含檔案 I/O 的通用測試工具帶進 #434 的受限 module 閉包。
- full／第二片的派送順序為 `P1161 → P1231 → P359`。P359 仍最後，P88→P72
  切點、storage handoff、兩片數量及原時限不變。
- `GEOMETRY_WORKSPACE_HEIGHT_ONLY=1` 只跑此段，屬 partial，不產生或更新 golden。
  T 的高度回歸用這個入口，避免被「新段尚未量得 count」的分片守門提前攔下。

## #434 尚未合入 main：本次補丁的路徑

T 已接好 driver／plan 與歷史守門；P 改產品版面。**本交付沒有手填 P1231 golden。**
現有 golden 原件為 99 段、5693 斷言、1553 bytes，LF SHA-256：

`cfbe3dc18bf983b3ea3d468c456c8dfddf33e893e5ed85916edfaa2be7e87bca`

先在隔離服務上跑 T，保存真正的高度或可達性斷言紅；套 P 後用相同入口轉綠：

```sh
GEOMETRY_WORKSPACE_HEIGHT_ONLY=1 node geometry-web/cdp_test.js
```

服務的 `GEOMETRY_TEST_URL`、`GEOMETRY_FEEDBACK_DIR`、Chrome 路徑與 bridge 均沿現行
AGENTS.md／CI 的隔離設定。測試服務不得指向使用者正在用的服務。T、P 各自的原始
stdout／stderr、exit、source head、尺寸與 `P1231_LAYOUT` 量測收據必須保存；
語法錯誤、缺模組、連不到 Chrome 都不是有效的紅。

### D：用原 full runner 產生新 golden

先把 T＋P 與 manifest 的逐檔來源審查提交在執行分支，清掉所有 partial／shard scope
旗標。下列 wrapper 要求受驗來源是乾淨的已提交版本，不接受只有工作樹修正的來源身分。

```sh
node tests/diagnostics/r16_canvas_golden.cjs --capture /tmp/r16-height-full-capture
```

輸出目錄必須在 checkout 外且尚未存在。工具沿現行 canvas job 的 **35 分鐘**上限執行
`GEOMETRY_CDP_UPDATE_GOLDEN=1 node geometry-web/cdp_test.js`，先驗證原 runner 的
full／零失敗／零 skip／完整 100 段順序與原 99 段逐值不變，再從該次結果取 P1231 的
精確 count。它保留原 99 段的序列化 bytes，只追加新段與總數；舊 byte pins 都不更改。
`original-full-writer.golden.json` 保留原 writer 的原始輸出，`capture.json` 記真 source head、
stdout／stderr 雜湊與前後 golden 雜湊。若任何一步拒絕，原 golden bytes 原樣還原。

此 capture 記 `acceptance:false`：它提供新段的完整實跑計數，尚不代表最終 head 的兩片
正式 CI 或 complete coverage 已通過。沒有真實成功結果時，golden 保持 99 段；正式分片、
完整覆蓋與新增外層投影應保持紅，不可用估算 count、fixture 或 partial 的 count 續綠。

原生守門的加法投影位於 `tests/diagnostics/r16_canvas_extension.cjs`。它先驗 P1231 的
唯一 owner、精確位置、真 golden 的正整數 count 與完整總數，才投影回原 99 段。
`test_canvas_shards.js` 的完整收據驗證仍使用實際 100 段；只有歷史 oracle 取得投影。
原 91／93／95／98／99 段的舊斷言與所有舊 raw-byte pins 繼續生效。

```sh
node tests/diagnostics/r16_canvas_golden.cjs --self-test
node tests/diagnostics/r16_canvas_golden.cjs --prove-guards /tmp/r16-golden-guard-proof
node --test tests/test_canvas_shards.js tests/test_identity_canvas_merge.js
```

第一條只跑 10 個合成 fixture 檢查；第二條實際撤回三個 guard，再還原，每個要求正常
AssertionError 的 `0／1／0`。這兩項不使用 Chromium，不能當成產品高度／遮蔽驗收。
第三條應在 D 完成後執行，count 保留現行兩 suite 的 41 與 4；本片沒有新增 native suite。
產品的高度與控制項具名撤回另由本片瀏覽器 runner 執行。

### 架構與不可變收據

`cdp_test.js` 的既有 exclusion 只更新這個已審來源的精確 hash；新增的
`workspace_height_test.js` 按測試 driver 登記獨立 exclusion，不做 directory exemption 或
refresh-all。兩支 diagnostics 在 `tests/`，不屬產品 JavaScript 的 search root。
由原 scanner 與架構測試重驗來源，再經 CI 原工具產生、採入 architecture bundle。
四個 frozen 歷史檔與正典閱讀器不手寫。mutation freshness 是否需新原件，仍以原
`evidence_records.py materialize`＋`tests/mutate.py --check` 判定。

## #434 先合入 main：改用正式片段流程

先讀合流後真正的 `tests/FRAGMENTED-REGISTRIES.md`。保留本片產品修改、DOM 契約及
完整 P1231 測試；**不恢復已退休的** `canvas_shards.json`／`cdp_sections.golden.json`，
也不再套用本片對 `cdp_test.js` 及兩支共享歷史測試的機械追加。
本片的舊格式 D wrapper／加法投影僅服務舊格式，不能拿來更新新格式歷史封存。

建立獨立 module `geometry-web/canvas_sections/P1231.js`：

```js
'use strict';
const run = require('../workspace_height_test.js');
module.exports = async helpers => run(helpers);
```

```sh
node geometry-web/canvas_registry.js stage-module --id P1231
```

T→P 與本片具名撤回的 partial 入口也改用通用 dispatcher：

```sh
GEOMETRY_CANVAS_MODULE_ONLY=1 GEOMETRY_CANVAS_MODULE=P1231 node geometry-web/cdp_test.js
```

舊的 `GEOMETRY_WORKSPACE_HEIGHT_ONLY` 接線不再存在；不可保留這個失效旗標而誤跑 full。
新 partial 仍不是正式 count／cost 收據，不能取代下列官方量測。

不加臆測順序依賴：本片自備場景，預設第二片尾 slot 仍在所有既有尾段之後、P359 之前。
候選零 count 不是 golden；用 `Canvas section measurement` 在本片分支真量測，再由可
下載官方 artifact 的 grokbot／本機 Claude 原樣導入：

```sh
node geometry-web/canvas_registry.js import-cost --id P1231 --artifact-id ARTIFACT_ID --artifact ORIGINAL.zip
```

測量 workflow 必須先隨 #434 進預設分支，才能 dispatch；雲端下載遭 403 時不得繞過。
初次保持第二片尾 slot；只有取得兩 slot × full／shard1／shard2 的正式 proof，才可使用
`import-slots`／自動平衡。不能拿本機耗時、斷言數或本片舊格式的 partial log 當成本原件。

新測試來源 `workspace_height_test.js` 與新 wrapper `canvas_sections/P1231.js` 各自登記為
`product-architecture.d/exclusions/` 下的獨立片段，產品 `workspace-height.js` 則登記為
`sources/` 的 H 層片段；schema／檔名依當時 reader。不再改 `cdp_test.js` 的新增派送或
其來源 pin，不手改已退休總表或改寫歷史封存。若本片先合入舊格式 main，
#434 的承接者必須在合流樹重跑原 `registry_migrate.py plan/apply/check`，把新 100 段真實
結果納入遷移輸入，不套舊 99 段的產物。

兩種格式都必須以最終合流 head 的原生守門、canvas 兩片及 complete coverage 為最後
驗收。片段化只改登錄方式，不降低 U123-H:A 的高度、可達性、具名撤回或來源驗真要求。
