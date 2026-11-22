# R16／U123-H:A：P1231 片段登錄與外部驗收交接

本文件回覆 issue #123 的 7064742253。來源基底是 main
`883e68688f6480a5f1de6e86e6a056cc20339cb9`；先前產品提交是
`38a86e71c03815b595fdb135d9d7cd62b9ba0500`。本次只處理登錄合流，
控制被遮住的產品問題由同 issue 7064969932 的增量修正接續。

## 來源與執行入口

- `geometry-web/canvas_sections/P1231.js` 是原
  `geometry-web/workspace_height_test.js` 的原樣搬移；本次未刪斷言、未延長等待。
- 模組以 `module.exports = async helpers => {...}` 輸出，使用既有
  `send`、`eval_`、`sleep`、`click`、`waitForUI`、`makeCheck`、`exceptionCount`。
  原 `sourceClosure(...,{strict:true})` 直接通過；沒有 fs、process、動態 require
  或 early observer，不依賴 #445 的新 driver 型別。
- `cdp_test.js` 保持 main 完整 bytes，沿 #434 的通用 dispatch。
- 片段由原命令 `node geometry-web/canvas_registry.js stage-module --id P1231` 產生。
  它是第二片最後一個獨立模組，順序 `P1161 → P1231 → P359`，切點仍是 P88／P72。
- `GEOMETRY_WORKSPACE_HEIGHT_ONLY` 已無接線。單段診斷一律使用：

```sh
GEOMETRY_CANVAS_MODULE_ONLY=1 GEOMETRY_CANVAS_MODULE=P1231 node geometry-web/cdp_test.js
```

這是 partial 診斷，不是完整驗收。測試仍完整包含五尺寸
390×844、768×1024、1400×900、560×844、561×844；教學展開／已讀、
六工作區與空間三視圖第二入口、真 Tab、控制五點、繪區 25 點、同一份
World／history、grid resize、visualViewport 分母、dock wheel 及 21c-1 文字堆疊。

## 三層精確對帳

1. 正式收據核對實際片段全集，P1231 的計數只能來自正式 Chrome measurement。
2. 精確只移除 P1231，得到 main 的 100 段、5718 斷言；P205 仍是 25，
   仍依 `P1284 → P205 → P353` 執行。其 1569 bytes 的 SHA-256 是
   `0acd8bdccce2eb3aae13b94bd04d9dfa89521dcd58d085e0e634698d4ca41e7b`。
3. 在歷史 oracle 的輸入中再精確移除 P205 的一行與 25 個斷言，得到原
   99 段／5693 斷言／1553 bytes；舊 pin 原值仍是
   `cfbe3dc18bf983b3ea3d468c456c8dfddf33e893e5ed85916edfaa2be7e87bca`。

不是 subset 比較：全部原段的值、順序、raw spacing 和唯一 owner 都仍受檢。
其他 PR 的獨立模組先以原 registry 載入器核 source closure／cost，再核完整
具名聯集與分片唯一性；只有歷史 oracle 的輸入才移除那些已登錄的其他模組。
未登錄段、重複 owner、遺失 P205、其他模組漏跑或計數漂移都會拒絕，
不會因 P1162 等獨立新段出現而改寫 R16 的歷史 pin。
兩支共享測試保留 R03 既有 oracle 和負控制，新增 R16 的精確投影與負控制；
沒有新增 native suite，也沒有改原 suite expected 計數。
`canvas-registry/legacy.*` 與 100 個既有 `cdp_sections.d` 片段保持 main 原件。
退休的 `canvas_shards.json`、`cdp_sections.golden.json` 不重建、不改寫。

## 官方測量與導入順序

目前 P1231 片段是 `provenance.kind=candidate`、`assertions=0`、`cost=null`。
0 是工具生成的未採用佔位，不是測試通過數；正式 `canvas_registry.js check`
與共享正式測試必須以 `R386_CANVAS_COST_RECEIPT_REQUIRED` 拒絕。

落檔者先合入 7064969932 的產品修正，提交乾淨完整來源，依
`tests/FRAGMENTED-REGISTRIES.md` 執行原 `Canvas section measurement` workflow，
輸入 `section=P1231`。保留官方 artifact 原 ZIP，不改其中 source、時間或計數。
導入只有這一條原正式流程：

```sh
node geometry-web/canvas_registry.js import-cost --id P1231 --artifact-id ID --artifact ORIGINAL.zip
```

原 R16 產生器也提供等效 adapter，直接呼叫同一個 `importCost`，不自行寫片段：

```sh
node tests/diagnostics/r16_canvas_golden.cjs --import-cost --artifact-id ID --artifact ORIGINAL.zip
```

新舊片段來源、官方 run、ZIP digest、count／cost、source closure 都由原 importer 重驗。
本機沒有 Chrome，沒有附測量值、成本、正式新 golden 或宣稱任何瀏覽器綠燈。
導入後提交完整來源，再跑完整模式與兩片／complete coverage。

## Node 可重跑檢查

```sh
node tests/diagnostics/r16_fragmented_alignment.cjs
node tests/diagnostics/r16_canvas_golden.cjs --self-test
node tests/diagnostics/r16_canvas_golden.cjs --prove-guards /tmp/r16-golden-guards-NEW
python3 -B tests/diagnostics/r16_height_mutations.py --preflight
```

`r16_fragmented_alignment.cjs` 的 P1231=17 僅在記憶體合成，不保存成任何正式檔。
它檢目前實際片段、P205 和原 99 段 pin、raw bytes、缺段、重複 owner、錯位、
模組 strict closure、cdp_test 與全部原片段 byte 相等，以及 pending 的正式拒絕。
這些是 Node 合成／來源契約結果，不能說成 Chrome 實跑。

`--prove-guards` 分別執行 `R16_WITHDRAW_LEGACY_BYTE_PIN`、
`R16_WITHDRAW_UNIQUE_OWNER`、`R16_WITHDRAW_CAPTURE_ZERO_FAILURES`，
要求三相退出碼恰為 0／1／0 並命中各自 oracle。
既有七項產品撤回保留，preflight 不代表七項已殺死；須在產品基準線真正綠之後，
用原 `r16_height_mutations.py` 各取真 Chrome 0／1／0。

## 導入後的正式檢查

```sh
node geometry-web/canvas_registry.js check
node --test tests/test_canvas_shards.js tests/test_identity_canvas_merge.js
node tests/diagnostics/r16_canvas_golden.cjs --capture /tmp/r16-full-NEW
```

`--capture` 現在是導入後的完整驗證：仍跑原 full CDP driver，35 分鐘上限不變，
要求 complete、zero failures、無 filters／modifiers／skip、逐段數與完整順序相等。
只把實跑 log、核對後 golden 與 receipt 寫到 repo 外；不寫任何登錄來源。
receipt 仍標 `acceptance:false`，最終 head 兩片與 complete coverage、其他正式 CI
必須另外全綠。`GEOMETRY_CDP_UPDATE_GOLDEN` 在此 adapter 明確拒絕。

## 架構來源

新增 H 層 `workspace-height.js` 來源片段及 P1231 模組的逐檔 exclusion pin，
兩者由 `architecture_contract.load_manifest`＋`fragment_manifest_files` 原編碼器產生。
不更新 cdp_test pin、不加目錄豁免；三份 architecture 衍生物及 freshness 證據
留給正式 evidence 流程重生與採入，不手寫。

## 層級

本次是候選補丁與 Node 驗證，沒有完成 R16 U123-H:A 的 L2／L3／L4。
當前仍待：可達性產品增量、正式 P1231 全矩陣、官方 cost 導入、七項真 Chrome
產品撤回、合流後完整 CI 與人工 App 核對。
