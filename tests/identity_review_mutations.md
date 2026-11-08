# #360 R09a：原生結算與產品入口的具名突變

審查基底：`8bc9f3f0298fcf6b4120dd1ea99ab30abd7da743`。本輪對應
`#360#issuecomment-6570352785` 的 B1～B3 與須改；沒有改公理或既有 golden 計數。

## 回歸入口

新增六個獨立 suite，共 46 項：native review 19、native fault 4、HTTP host 4、
content contract 7、native/ContextHistory 3、JS recovery/exchange 9。既有
`py:test_identity_ledger` 16、host shape 5、`node:identity_ledger` 13 原封保留。

```sh
python tests/run_all.py --build --only identity
```

這是有明確範圍的部分執行，不代表整個 repository 或真瀏覽器驗收。新增 Node suite
由 `NODE_NATIVE_TEST_FILES` 獨立註冊，使用 fresh bridge；沒有灌進既有 Node aggregate。

`test_identity_ledger_review.py` 的 L08 先以有合法 placement/place 的完整場景在新
原生行程成功重開，再逐格破壞身分宣告。拒絕必須有對應 I70／I71／I72 診斷，且完整
World 與帳本不變；I9 的未放置角材拒絕不能代替身分驗證。L21 各原生批次先驗新卡
確實結算、同值重宣告不配號，再驗明示刪除／重建換記號、內容 hash 不變但歷史改變。

## 原生突變表

14 個正式突變列在 `tests/mutate.py` 的 `MUTANTS`，每列均 `binary="bridge"`，指定的真原生
方法均已列入 `tests/mutation_bridge.py` 的 `RESTORED`。它們改實際 C 產品程式，
沒有把舊 JS `settleKey` 探針當成 `g_world`、候選序列化或配置器的證據。

表內 `review` 指 `tests.test_identity_ledger_review.IdentityLedgerReview`，`faults`
指 `tests.test_identity_ledger_faults.IdentityLedgerFaults`；「L21 四路」就是
`test_L21_{engineering,assembly,generation,section}_same_key_rebuild` 四個方法。

| ID | 被移除的實際產品防線 | 指定方法／殺點 |
| --- | --- | --- |
| `R09A_N01_ZERO_ID_REOPEN` | 載入解析器改回全面拒絕 id 0 | review `test_B1_zero_ids_save_and_reopen_in_a_new_process`；`B1_ZERO_ID_REOPEN` |
| `R09A_N02_EXPLICIT_DELETE` | 結算忽略 explicit-delete | L21 四路；`L21_EXPLICIT_DELETE_*` |
| `R09A_N03_COUNT_REBIRTH` | 預計需用序號漏算重建鍵 | L21 四路；`L21_COMMIT_ALL_NEW_SERIALS_*` |
| `R09A_N04_PREVIEW_DELETIONS` | 候選確認遺失明示刪除集合 | L21 四路；舊記號不得沿用 |
| `R09A_N05_PARAMETER_DELETE` | 刪卡漏記卡的明示刪除 | L21 四路；卡記號必換 |
| `R09A_N06_FIELD_DELETE` | 刪卡漏記欄位的明示刪除 | L21 四路；兩欄記號必換 |
| `R09A_N07_BATCH_SETTLEMENT` | 實際 batch finalize 不結算帳本 | L21 四路；`L21_NATIVE_BATCH_SETTLES_NEW_KEYS_*` |
| `R09A_N08_LINE_NOOP_RECEIPT` | 成功的同值 line 一律報 changed | review `test_B3_line_noop_receipt_matches_native_undo_active_and_inactive` |
| `R09A_N09_DRAG_NOOP_RECEIPT` | 成功的零位移 drag 一律報 changed | review `test_B3_drag_noop_receipt_does_not_consume_history` |
| `R09A_N10_REPLACEMENT_EPOCH` | 整體取代保留舊 epoch | review `test_S1_whole_replacement_clears_epoch_only_on_success`；reset/default/loadfile/load-confirm |
| `R09A_N11_DERIVED_COVERAGE` | 涵蓋集合再次排除 derived placement | review `test_S2_derived_placement_covered_and_cold_reopened`；`S2_DERIVED_COVERED` |
| `R09A_N12_DERIVED_DELETE` | 移除 derived placement 的明示刪除回呼 | review `test_S2_derived_explicit_delete_rebuild_is_new_incarnation` |
| `R09A_N13_CHANGED_INCLUDES_MARKS` | changed 只看去身分定義 hash | L21 四路；`L21_MARKS_ARE_CHANGE_*` |
| `R09A_N14_CONTINUED_MARKS` | 延續鍵無條件重新配號 | L21 四路；既有記號與同值 no-op 必須不變 |

已提交補丁之後，可由既有正式工具使用官方編譯旗標、獨立 checkout 及正式帳本執行：

```sh
python tests/mutate.py R09A_N01_ZERO_ID_REOPEN R09A_N02_EXPLICIT_DELETE R09A_N03_COUNT_REBIRTH R09A_N04_PREVIEW_DELETIONS R09A_N05_PARAMETER_DELETE R09A_N06_FIELD_DELETE R09A_N07_BATCH_SETTLEMENT R09A_N08_LINE_NOOP_RECEIPT R09A_N09_DRAG_NOOP_RECEIPT R09A_N10_REPLACEMENT_EPOCH R09A_N11_DERIVED_COVERAGE R09A_N12_DERIVED_DELETE R09A_N13_CHANGED_INCLUDES_MARKS R09A_N14_CONTINUED_MARKS
```

提供另一個可在未提交補丁樹執行的定向入口：

```sh
python tests/identity_native_mutation_check.py --list
python tests/identity_native_mutation_check.py --output /tmp/r09a-native-evidence --native-output /tmp/r09a-native-binaries
```

此入口使用同一張原生突變表、官方 `binaries.py`、實際 bridge oracle 與嚴格
`mutation_bridge.classify`。POSIX 編譯旗標明列為 `-std=c11 -O0`，每筆都跑
基準／具名突變／還原；輸出有來源閉包、二進位與 sidecar、裁判、原始輸出雜湊。
它的 JSON 明示 `official_ledger:false`，不讀、不改、不捏造 `tests/mutants_results.json`。
只把完整執行的行為 AssertionError 算 killed；編譯、載入、KeyError、當機、skip 或
不完整報告均不能算 killed。最後可接一個或多個 ID，只重跑尚待解決的定向風險。

### 另外兩個私有原生故障突變

這兩列在 `identity_native_mutation_check.py` 的 `PRIVATE_FAULT_MUTANTS`，明示
`binary="private-fault"`。它們不列入正式 `MUTANTS` 或 `RESTORED`，也不寫正式帳本。

| ID | 被移除的實際產品防線 | 指定方法／殺點 |
| --- | --- | --- |
| `R09A_N15_PENDING_NOT_COMMITTED` | 暫配未通過驗證就推進正式序號 | faults `test_P053_failed_settlement_after_temporary_allocation_consumes_nothing` |
| `R09A_N16_INCOMPLETE_DUMP` | 放行不完整帳本的完整 dump | faults `test_L20_incomplete_world_refuses_full_dump_but_can_export_and_undo` |

```sh
python tests/identity_native_mutation_check.py --private-faults --list
python tests/identity_native_mutation_check.py --private-faults --output /tmp/r09a-fault-evidence --native-output /tmp/r09a-fault-binaries
```

私有模式從每一個當下來源（基準／mutant）編譯真正帶故障鉤子的 O0 binary，記錄
實際 binary SHA-256、原生閉包、helper SHA-256 與三個生成 C/include 檔的 SHA-256。
給 `bridge_mutation_oracle.main` 的 binary argv 和給 fixture 的
`GEOMETRY_IDENTITY_FAULT_BRIDGE` 必是同一路徑，因此 ChildWatch、裁判與實際受測
行程一致。還原來源後再用已核對 SHA 的原基準 binary 跑具名方法。沒有使用另一支
官方 O2 binary 的 sidecar 冒充私有 O0 程式。

故障 suite 在暫存真原生來源插入私有命令：從已提交帳本漏一筆、設定序號高水位、
讓真 `identity_table_ok` 拒絕暫配結果。沒有自寫配置器、假原生回覆，產品不帶故障入口。

## 產品入口的獨立具名突變

這些控制改真 JS/Python 產品程式的私有記憶體或暫存副本，保留真原生 World；
不改 repository 產品檔，也不替代上方 14 列正式及 2 列私有原生突變。

### 前端 no-op 歷史

```sh
IDENTITY_CONTEXT_MUTANT=B3-NOOP-HISTORY GEOMETRY_TEST_BRIDGE=/path/to/fresh/bridge node --test tests/test_identity_context_history.js
```

移除 `ContextHistory.observe` 的 `history_changed === false` 防線，三項分別在
`B3_NO_PHANTOM_LINE_HISTORY`、`B3_NO_PHANTOM_DRAG_HISTORY`、
`B3_NOOP_GROUP_IS_CLEAN` 斷言紅；來源附件與 id-map 實際和原生 undo/redo 對照。

### 去身分內容與恢復

執行範本（未指定 fault bridge 時會以本樹來源編譯私有真原生工具）：

```sh
IDENTITY_RECOVERY_MUTANT=L20-HANDSHAKE node --test --test-name-pattern='L20 alpha' tests/test_identity_recovery_contract.js
```

| ID | test-name-pattern | 具名行為證據 |
| --- | --- | --- |
| `L20-HANDSHAKE` | `L20 alpha` | 真完整 dump 拒絕時連線仍應 ready |
| `L20-LOADING-ALLOWLIST` | `L20 alpha` | loading 白名單必容許去身分 dump |
| `L20-PROBE-FULL` | `L20 alpha` | 第一探測應恢復 metadata，不得因完整 dump 拒絕變 mismatch |
| `L20-PROBE-HASH` | `L20 gamma` | root 與 receipt 恢復用去身分探測，保存仍留完整 sceneHash |
| `L20-INCOMPLETE-SAVED` | `L20 alpha` | 漏帳恢復只能未保存／dirty，不能覆蓋先前 ZIP |
| `L12-STRIP-REQUIRES` | `L12 native-backed` | 本地剝除結果與真 native 去身分 bytes 相等，包括空帳 |
| `L12-EXPORT-FULL` | `L12 actual scene` | 正式匯出 Blob 不帶帳本 |
| `L12-FEEDBACK-FULL` | `L12 actual scene` | 正式 feedback POST 的 world 不帶帳本 |
| `L12-MODEL-FULL` | `L12 model` | 真 model source owner 讀取有效且去身分的 sourcePin |
| `L10-PARAMETER-DEFINITION-ALLOWLIST` | `L10 actual` | 正式 ParameterUI.exportPackage 的 Blob 只含可交換定義、不漏計算快取，原文可送原生刪後匯入並取新記號 |

這十種的測試子行程應以行為紅結束（exit 1）；去除變數後九項全綠。
真 ZIP、hash、native API、正式 JS owner 都執行；DOM、IndexedDB 排程、Web Locks、
HTTP transport、PDF renderer 是明列受控接縫，沒有宣稱 Chrome。

### 真 HTTP 宿主配號區段

```sh
IDENTITY_HOST_MUTANT=L25-STARTUP GEOMETRY_TEST_BRIDGE=/path/to/fresh/bridge python -m unittest tests.test_identity_host_runtime.IdentityHostRuntime.test_L25_startup_public_rejection_and_interactive_history_keep_host_epoch -v
```

下表方法均在 `tests.test_identity_host_runtime.IdentityHostRuntime`，名稱前綴 `test_L25_`。
每個都啟動正式 `serve.py`，以真 HTTP 與真 NativeContext 驗實際新記號的 epoch prefix。

| ID | 方法後綴 | 具名行為證據 |
| --- | --- | --- |
| `L25-STARTUP` | `startup_public_rejection_and_interactive_history_keep_host_epoch` | 啟動即裝配 epoch |
| `L25-REPLACE` | `every_successful_http_whole_world_replacement_reseeds_without_rewinding` | 五條成功取代路徑各換新區段、序號不倒退 |
| `L25-PUBLIC-EPOCH` | `startup_public_rejection_and_interactive_history_keep_host_epoch` | 頁面不能設定宿主 epoch |
| `L25-FAILED-LOAD` | `prepare_cancel_and_failed_loads_keep_epoch_world_and_serial` | 失敗載入保持原區段 |
| `L25-PREPARE` | `prepare_cancel_and_failed_loads_keep_epoch_world_and_serial` | prepare 保持原區段 |
| `L25-CANCEL` | `prepare_cancel_and_failed_loads_keep_epoch_world_and_serial` | cancel 保持原區段 |

上述六種應行為紅（exit 1）；去除變數後四項綠。另第四個正常見證真的建立
scenario 第二原生行程，確認子行程區段獨立、root 不被換段。

### 模型、場景 capability 與 rule-case

```sh
GEOMETRY_TEST_BRIDGE=/path/to/fresh/bridge GEOMETRY_MODEL_BASE=/path/to/fresh/model-base python tests/identity_content_mutation_check.py . L12-NATIVE-CAPABILITY
```

| ID | 實際被改的產品防線 | 精確殺點 |
| --- | --- | --- |
| `L12-NATIVE-CAPABILITY` | `scenario_verify.NATIVE_CAPABILITIES` 擴收帳本 | `L12_MODEL_CAPABILITY_MUST_NOT_BE_WIDENED` |
| `L12-MODEL-DEFAULT` | `_capabilities` 預設改用 bridge capability | 該模型路徑必拋 `ModelError` |
| `L12-RULE-CASE-FULL` | 真 executor 兩處 `dump-deidentified` 改為 `dump` | `L12_RULE_CASE_DEIDENTIFIED_COMMAND` |
| `L12-STALE-DUMP` | HTTP stale 白名單漏去身分讀取 | `L12_STALE_HOST_MUST_ALLOW_DEIDENTIFIED_DUMP` |

此 runner 只在「一個指定方法、零 error、恰一個指定 assertion 紅」時輸出
`killed-by-named-assertion` 並 exit 0；這個 0 是對紅證據的核驗成功。模型、D25、
完整場景及 executor 正常七項另跑；stale HTTP 一項明列 controlled pipe，沒有
將它宣稱為真 native freshness 故障。它也不寫原生 mutation ledger。

## 環境界線

四項自查為語法、頁面字串編譯（含 async 數）、registry、完整 `app.js` Node VM
載入；後者明列 DOM/browser shim，必到 EOF init 且有 undefined-global 負控制。
它們不能替代 `identity_ledger_browser_test.js` 的真 Chrome、Windows GDI
或全 repository CI。這些仍由實際具備環境的驗收完成。
