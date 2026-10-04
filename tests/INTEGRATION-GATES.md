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


## #46 獨立快照模組的登錄與外部門檻

snapshot/diff/review-native 三個 Node 檔（23／18／18）加入
NODE_TEST_FILES，完整 census 發現 Node 374 → 433；Python
test_scenario_verify 35 tests 加入 PY_NEEDS，要求 fresh bridge＋model-base。
既有 floors 及 ALLOWED_SKIPS 不變；新增數量取自完整 census，不以空腳本或 skip 補足。
Linux cloud 的完整 candidate census 在 process-local 16 MiB stack 下實跑；
8 MiB stack 曾使未修改的 native integrity／subgrid 基線崩潰，不能用它的 fail／skip
調低 floor。owner 套用登錄後，POSIX 的正式凍結 head 驗收命令為：

    ulimit -s 16384
    python tests/run_all.py --build

本 patch 的 candidate census 不能替代正式已發布 runner 在最終 head 的 strict 驗收。
這些測試只證明獨立快照／原 bytes／格式／origins／隔離 native 核驗，
不代表產品 A/B 入口、whole adopt 或 recoverable history 已完成。

以下兩個既有腳本在 NODE_EXCLUDED 逐檔登記原因，aggregate 未執行、
不計 pass/skip；仍須另外執行並保留證據。

先用 tests/binaries.py 建置 receipt-backed runtime；一般 npm .build 產物
沒有這份 freshness receipt，不能替代。Playwright／Chromium由驗證環境提供。

    python tests/binaries.py build bridge model-base
    GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base node tests/scenario_browser_check.cjs

這是 ephemeral loopback 的獨立 module browser gate：1280／390、
真正 ZIP download／file input 重開、原 bytes、B 不改 A、fork／replacement diff、
latecontext／tamper；禁止 live upload。沒有正式產品 UI/adoption 的驗收語意。

    GEOMETRY_SCENARIO_PROJECT_MODULE=/absolute/path/to/actual-owner/project-store.js GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base node --test tests/test_scenario_grid_interface.js

GridDraft 使用真正 owner project-store／同目錄 feature-attachments validator；
PR104 尚未在 main 的這個 slice 維持注入 interface，
不是以 unsupported 丟棄已批准 raw 草稿。缺 owner 注入時原腳本的具名 skip
絕不能當 compatibility pass，也不加入 ALLOWED_SKIPS。
真正 validator 必須實跑 raw 非法／未完成輸入、獨立 A/B、ZIP 重開、unknown kind/cap 拒絕。
正式 saving adapter 合 main 後，owner 再把此檔移入 NODE_TEST_FILES、重做 census；
不能在本 patch 預先假算第 434 項。

Linux cloud 的 scenario Python suite 為 35/35；Windows 目前有 8 個
temporary-shebang fixture skips。這些沒有平台豁免，Windows strict 會拒絕全過；
須由後續 test owner 解決 fixture portability，不能使用 allow-skip 冒充完整驗收。

## #116 B 情境選單

`tests/test_issue116_browser.js` 是必跑的真原生／瀏覽器 gate，獨立於非瀏覽器 aggregate。
提供隔離 `GEOMETRY_TEST_URL`、TEMP `GEOMETRY_FEEDBACK_DIR`，並以 `NODE_PATH` 指向
既有 Playwright runtime（本機可用 Codex bundled packages），執行 `node tests/test_issue116_browser.js`。
它驗 `/runtime` repository/fresh、真右鍵及數值欄位、取消不改、精確凹口確認、單步 undo/redo、
完整 `.gcanvas` 保存／重開、過期上下文拒寫、鍵盤及搜尋、孔邊快捷限制與核心角色拒絕、390/720px 可達性。
截圖／驗證專案只寫 TEMP；不寫使用者 feedback 或已提交 golden。
另跑無 scope flag 的 `geometry-web/cdp_test.js`，包括原選取／游標及所有既有共用介面回歸。
PR #114 正式多房間 owner 與實體 iOS／IME／系統選檔仍須 dot 整合後驗收，不能以本 gate 代替。
