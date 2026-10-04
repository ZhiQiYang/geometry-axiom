# 非瀏覽器登錄與必要正式整合驗證

`python tests/run_all.py --build` 嚴格執行已登錄的非瀏覽器 suites，
逐 suite 比對 `run_all.expected.json`。exit 0 只證明這個範圍，
不代表尚未接上產品的模組或下列正式整合驗證已完成。
既有 floors、具名平台 skip 清單與實際測試斷言維持。

## #44／#77 新增模組的實際登錄

| 原測試檔 | 非瀏覽器實際測試數 | 執行方式／範圍 |
| --- | ---: | --- |
| `test_model_update.py` | 22 | 真 bridge 與 model-base；獨立 Python suite |
| `test_model_update.js` | 39 | 模型更新契約、隔離候選及控制器 |
| `test_room_collection.js` | 31 | 房間集合／控制器；原有私有暫存編譯 bridge 和測試 owner fixture 保留 |
| `test_issue77_workspace.js` | 6 | 工作區模組；不是產品 app 接線驗收 |
| `test_issue77_attachment.js` | 4 | 純 payload／native-reference 契約；正式 owner 五項完整移至下列入口 |

四個 Node 檔共 80 tests，既有 `node:tests-js` 294 → 374。
Python 新增獨立 22 tests，不併入 Node 數量。
共同自製 PDF/payload 夾具 `issue77_attachment_fixture.js` 不註冊任何 test，
不把 Node 對空腳本的假性一項成功計入 floor。

## #77 必需的正式 owner 五項驗證

入口 `tests/integration/issue77_attachment_owner.js` 保留原五項完整斷言：

1. 真 ZIP roundtrip 與原 PDF 恰保存一份，重開再保存仍保留 attachment。
2. 未知 envelope version、kind、schema、capability、缺能力及重複 kind 拒絕，不能靜默丟資料。
3. 來源閉包與最終 native object hooks 拒絕遺失來源／房間引用。
4. ContextHistory rename、unlink、native delete、同 ID undo/redo、unknown history 快照。
5. 讀寫 context guard、遲到寫入隔離及房間 metadata 與 native 同一步交易。

正式 `source-rooms` owner 接口尚未實作時，直接執行：

```sh
node tests/integration/issue77_attachment_owner.js
```

入口輸出機器可讀 JSON：`status: pending_implementation`、
`required: 5`、`executed: 0`、`passed: 0`，逐項列出缺口，exit 3。
這是實作缺口，不是環境受阻、skip 或 pass；不加入 `ALLOWED_SKIPS`。
`run_all.py` 顯示這個必需入口與範圍，不在非瀏覽器合計中假算五項。

owner 實作後，以 test-only shim **映射真產品 registry／envelope／pack／unpack／history／transaction API**：

```sh
GEOMETRY_ISSUE77_ATTACHMENT_TEST_ADAPTER=/tmp/real-owner-shim.js \
  node --test tests/integration/issue77_attachment_owner.js
```

shim 不得另造 store／ZIP envelope／history 來取代正式接線。
配置了 shim 卻少必要方法會立即 setup fail（exit 1），不允許跳過。
只有這五項真 owner gates 全部實跑通過，才可聲稱 attachment 正式整合通過。

## #77 必需的四個真瀏覽器入口

以下四個腳本使用 Playwright、實際 Chromium、app 與 native；不是 `node --test` suites。
它們在 `NODE_EXCLUDED` 逐檔登記具體原因，非瀏覽器合計**未執行、未驗證**，
不把 script 未跑或臨時 prototype adapter 成功當產品整合完成。

```sh
GEOMETRY_TEST_URL=http://127.0.0.1:18951/ \
GEOMETRY_FEEDBACK_DIR=/tmp/issue77-formal-feedback \
  node tests/test_issue77_browser.js
GEOMETRY_TEST_URL=http://127.0.0.1:18951/ \
GEOMETRY_FEEDBACK_DIR=/tmp/issue77-formal-feedback \
  node tests/test_issue77_exit_browser.js
GEOMETRY_TEST_URL=http://127.0.0.1:18951/ \
GEOMETRY_FEEDBACK_DIR=/tmp/issue77-formal-feedback \
  node tests/test_issue77_recovery_browser.js
GEOMETRY_TEST_URL=http://127.0.0.1:18951/ \
GEOMETRY_FEEDBACK_DIR=/tmp/issue77-formal-feedback \
  node tests/test_issue77_remove_browser.js
```

先以目前 exact head 的隔離服務驗 `/runtime` 與 fresh binary closure；
回報／截圖／browser profile 放 TEMP，不使用使用者服務或私人圖紙。
正式產品須提供 RoomCollectionWorkspace、來源／房間 UI、F attachment 接線、
草稿離開及恢復的 owner guard、實際完整 ZIP 保存重開。
`GEOMETRY_ISSUE77_BROWSER_ADAPTER` 是明示的 prototype evidence 選項；
若使用，報告必須標 prototype，不能代替上述正式 owner 五項驗證。

既有 `geometry-web/cdp_test.js` 與 `geometry-web/space_model_test.js`
仍另外執行，各自完成及 floor 相符才是其範圍的證據。
