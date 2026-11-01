# 非瀏覽器CI確定性分片（2026-11-02）

使用者同意修改P-186的執行安排：三個native矩陣job同時執行，每個`timeout-minutes: 35`保持。以main `405f8c5e1a637a16cbe47470faf5ae1fa02b8676` 的[原GitHub native job](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/40185639126/job/124015759512)逐suite耗時配置，目標每片實跑低於20分鐘；不延長期限、不豁免失敗。

`native_shard_timings.json`保留完整來源SHA／run／job／原log SHA256及224個suite的實測毫秒。按耗時遞減、名稱破同分，指派至目前累計最小的片（再以片號破同分）；片內保留原完整runner的順序。新suite沒有歷史權重時用1000ms，仍必分到某片。配置不依本機cache、即時耗時、亂數或Python hash seed。

```sh
python3 tests/run_all.py --build --shard 1/3 --report /tmp/native/shard-1.json
python3 tests/run_all.py --build --shard 2/3 --report /tmp/native/shard-2.json
python3 tests/run_all.py --build --shard 3/3 --report /tmp/native/shard-3.json
python3 tests/native_shard_receipts.py --input /tmp/native --parts 3 --output /tmp/native-complete.json
```

上述三個runner命令由不同GitHub job執行。單一片只代表該片，不能獨自宣稱完整驗收。`native complete coverage`下載三份原始收據，核對同一完整checkout SHA、耗時表／expected雜湊、計畫與實跑套件清單；每列必實跑、無fail／crash／環境問題、數量等於原expected、計數守恆。各片suite聯集必須等於原完整registry，且彼此不重疊。三份收據缺一、重複、漏列、來源不同、片內耗時達20分鐘均拒絕。GitHub各job由setup至complete的時間另外直接由Actions API核對，不把suite時間冒稱全部job時間。

完整suite清單維持拆分前的224個；沒有因新增守門增加或移除suite。11個新守門測試併入原`py:test_unittest_runner`，expected僅將該套1改12，其他expected不變。`check_registry`仍在每片執行；selected suite逐列嚴格比數量，另以完整universe檢查expected中已不存在的suite。`mutation:check`保留原套件、原指令、原退出碼及嚴格度，恰在某一片執行；不因分片跳過它。

每列另保留真實子程序`process_exit_code`，彙總必須收到整數0；缺失、布林、非0、未啟動或逾時的空值均拒絕。帳本inventory沿用原本的零斷言計數，不能偽造為一個通過斷言；其餘僅退出碼腳本保留原通過計數1。負控制同時驗證原runner記錄真實退出碼與彙總拒收偽綠列。這項修正來自首輪真CI彙總誤拒inventory的實際紅燈；不是放寬原mutation檢查。

```sh
python3 tests/native_sharding_mutation_check.py --output /tmp/native-sharding-proof
```

此GitHub CI反證使用同一支真實`test_partition_covers_actual_suite_registry_once`：基準exit0；只從其中一片拿掉一個suite，必須以該測試的正常AssertionError紅exit1（非error／skip／timeout）；恢復後exit0。原始0／1／0、移除的suite與stderr均上傳artifact。

`--shard`拒絕與`--only`／`--extra-py`／`--simulate-missing`混用，也不能更新expected。原`--allow-skip`的人工用途及具名允許清單不變；CI不設它，彙總只接受原允許skip。

本機只編輯與靜態檢視，所有執行、反證及效能量測以GitHub Actions原收據為準。新tests Python會使bridge突變裁判雜湊過期；必須由GitHub真重產完整帳本並保留原strict check，不手改hash或當成環境豁免。

## R06 分支的同一基礎設施

R06 以 `bf178770a0e10e996014ec0b6487e186db561c7f` 的純 CI 差異三向套用，保留 R06 新增的兩個 Python suite，故本分支是 226 套。完整 [Actions run 41335411500](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41335411500) 的三份原始收據為 75／76／75 套，聯集精確等於 226、全部 ran、無重疊；記錄的 suite 時間為 727.680／730.221／427.026 秒。這次仍有真實回歸與舊 mutation ledger stale，不能當作驗收綠燈。

依該完整 census，只補上新 suite 的實際發現數 48／7，以及 Node aggregate 737→753；其餘原數量不變。Node 22 的 `node:test` 非隔離 run 沒有套用本 adapter 所需的名稱篩選，嚴格控制正確回報完整性錯誤；native CI 與 R06 專項一致明確選 Node 24，保留同一篩選、精確 test stream 與負控制，不把全部測試的錯誤當成指定案例的 kill。
