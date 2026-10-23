此變更只縮短 workbench HTTP 測試 fixture 等待關閉的輪詢間隔。每個方法仍各建自己的 server/session；原 handler、adapter、shutdown/close/join、19 個測試方法與全部斷言、產品期限均保留。尚未量測實際收益。

| 唯一 current-state 項目 | 固定來源／結果 |
|---|---|
| 來源 S | `2199cda8896b47c7ad2b6c10479e5e0cbdb67c83`，已一般 push 且遠端同 SHA |
| 基底 E | `3c6633575ec0f9dccf35898380202aad8d0ffddf`；只改 `tests/test_rule_case_workbench_http.py` 一行 |
| 原件 evidence head | `9896410a84b31fb742b5e92bc5601715bf242267`；`evidence/issue214-fixture-2199cda8/`，完成準備與runtime物化原件完整封包、逐 member roundtrip |
| 單檔獨立靜審 | 14 checks／0 findings；只代表準備接受，非執行通過 |
| helper 獨立靜審 | 20 checks／0 findings；AST/身份/原期限與完整方法核對，非執行通過 |
| 原整套 workbench HTTP 正式驗收 | **UNRUN**；原 19 方法、原 Python suite 時限 1200 秒，零新增 skip |
| component／CPU／wall 量測 | **UNRUN / UNMEASURED**；不新增性能合格門檻 |
| 撤回／恢復 | **UNRUN**；poll 優化撤回語意應等價，不冒稱功能突變 kill |
| 完整 native／其他 job | 本分支尚未執行，這個 19 方法切片不能取代它們 |

候選在測試的 `Thread` 明示傳入 `serve_forever(poll_interval=0.05)`，取代標準庫預設的 0.5 秒 shutdown 輪詢。這不是 HTTP/native 回覆期限；既有 15/30 秒產品期限、5/10 秒事件及 join 期限沒有變。`tests/test_serve.py` 的 51 方法不在本片。

量測 helper 與原始驗收分開：正式 row 沿原 `tests/run_all.py --build --only test_rule_case_workbench_http`，完整選既有 19 方法；component 診斷沿未改的 `_unittest_runner` 與原 1200 秒 watchdog，透明量 setUp/tearDown、shutdown、join、adapter.close，不能把它冒成原 run_all row。server_close 內嵌 adapter.close 的 inclusive 時間不重複加總。測試尚未執行；helper 已由第二人靜審 20/0。

原／候選／等價撤回／恢復的 correctness 都應通過。收益可以為 0 或負；沒有把 8.55 秒估算當實績、沒有改 timer、刪案例、改 expected/golden 或新增性能門檻。更密集的空閒喚醒可能增加 CPU，需由原樣本如實判讀。

Linux bridge/build/log cache 仍是原 `/tmp/geometry-tests`；TMPDIR 不能把它隔離。動態驗收須等 root 配置獨立 runtime 與共享 cache 租約，不能與完整 native／required-eight 的 cache 寫者並跑。隔離來源已物化 834 個固定 Git 檔（約 16.5MB allocated），S 與完整 index tree 不變；未編譯、未跑 native／HTTP／Chrome／bench，也沒有把較早列車的綠燈移到此 S。

這是 #214 的 A4 工程切片，不代表整件 #214 或全專案完成；不更動主列車、公理與決策，不合併 PR。

準備原命令中的 commit 後 7 筆身份標籤更正另保留於包內 `SOURCE_AUDIT_BINDING_ADDENDUM.json`；原始 streams 不改，沒有將準備命令冒稱測試執行。
