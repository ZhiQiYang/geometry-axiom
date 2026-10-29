# #348 F0f695866：H7／W7 與三組 helper 反證執行計畫

**尚未啟動。** 固定來源 `0f695866c0ba12d2c70dfd7d40628d0fda0f905f` 已普通推送，公開後 peer111/0。測試來源／generator 曾做 AST 與 bytes 檢查，沒有執行。root 優先排本項，但目前約49～60MiB磁碟不足原100MiB環境guard；不盲啟C。新 raw collector 唯一owner為 evidence_resume，完成後交 train_review 找錯。本計畫不把尚未完成的collector列成可執行驗收工具。

## 真正原入口與序列

原正式入口均使用 **F 原封不動** 的 `tests/_unittest_runner.py`，每個是獨立子程序，保真正退出碼：

```text
python3 -B tests/_unittest_runner.py tests/test_geo261_timber_capacity.py --json-out <OUT>/W7/runner.json --log <OUT>/W7/unittest.log
python3 -B tests/_unittest_runner.py tests/test_geo261_timber_capacity_host.py --json-out <OUT>/H7/runner.json --log <OUT>/H7/unittest.log
```

兩份 runner JSON 都必 total=run=passed=7、failed/skipped/blocked_by_error/expected_failed=0，進程exit0；不能只數stdout的PASS字樣。先W再H，紅燈仍保留並完成可獨立執行項。H的七ABI控制刻意使compiler非零，所以不能用「所有compiler0」當整份H裁判。

三個新測試修正，各在**獨立 phase 子程序**做固定0／撤回1／恢復0，不能只把Python函式回傳1冒OS退出1。原選定方法入口：

```text
python3 -B -m unittest -v tests.test_geo261_timber_capacity_host.TimberCapacityHost.test_each_real_declaration_retains_legacy_64_and_admits_up_to_512
python3 -B -m unittest -v tests.test_geo261_timber_capacity_host.TimberCapacityHost.test_full_capacity_redeclaration_replay_and_rejected_edit_preserve_history
```

第一條用於count控制；第二條分別用於population、unplaced_replay控制，各三phase，不同時撤兩項。精確before/after位於 `host-v5-draft/EXACT_WITHDRAWALS.json`，施加前要求after恰一處，恢復後測試檔逐bytes等F。只在新私有正式checkout修改這一個test helper，不能碰公開branch工作樹、產品或runner。每phase都保存原測試檔、變體檔、完整diff與hash、HEAD F、dirty狀態及source_variant；撤回變體不冒clean F。

count首紅必位於count64的 `assert_count`，原objects只回空placed列表，正常AssertionError含預期ID序列與[]。population首紅必是舊load_full對未放置scene期待ok=true，真I9錯誤可在原bridge回覆／stderr確認。unplaced_replay只撤末端重放處，前面population和count修正保留，必在原I9拒絕處正常AssertionError；不能用population先紅取代它。每份負例必只啟動指定一個方法、normal failure=1、無error/skip/unexpected success、無編譯錯／timeout／signal死亡；若實際首紅不同就分類，不冒反證成功。

此階段是兩套正式7＋7和三組測試修正控制，不等於局部75整組、完整native、六browser、P189、stack或帳本已驗。其餘原contact12/contact_sources15/declaration9/validation14/report11仍須依root最後closure安排。

## 原控制怎麼核

- W原三個guard控制：validation／declaration capacity／existing identity，逐個原named `ASSERT:...\n`、正常C exit1，前後原client exit0；不吞compiler失敗。第四個容量值控制只建values-only TU，宏64與還原512均不混產品ABI。
- H原safe guard控制只有缺ID sentinel；撤guard的child仍正常存活，具名PythonAssertionError由原test捕獲並打印。這是framework紅，不冒C child exit1，也不送valid513越界。
- H七ABI控制分別world/timbers/anchors/contact/report/span/faces。每個fixed編譯0、withdrawn非零且含指定 `app_timber_capacity_*_check`、restored編譯0；預期失敗物件不link／run。原真正compiler argv、stdout/stderr及**當時**的C/quoted-header bytes都封存，不能只保存恢復後header。
- 新真placed N64/512、canonical fresh replay bytes、512逐line/513拒絕與undo/redo是H7內兩方法；原600秒是新方法沿P189既有sample timeout，舊10秒及其他原限制不改。超時原樣紅，不追加更長重試來冒原gate過。

## 原流／隔離與collector前置

沿原 c387 recorder 與 reaper7d848；原 #346 driver在 `/tmp/geo300-cut-list-storage-20261024/formal-tools/{launch_report_suite.py,run_report_suite.py,retain_report_streams.py}`，只能參考框架，不能原封稱適用H。原run observer保存text時明列decoded-text-encoded-UTF8，不冒pre-decode bytes。新collector必另捕 BridgeSession 的Popen pre-decode stdin/stdout、完整stderr、真child terminal，並保存run_once的input.bin；不重序列化JSON代替原流。compiler-negative的header需在實際compile前快照，原NativeBuild cleanup logs／C sources另保。

collector自驗須先過且獨審，不能用產品初跑檢驗collector可靠度：LF/CRLF、UTF-8分段、預讀、stderr、真非零、EOF、BrokenPipe／timeout語意應與原接口一致。新的collector缺件、觀察異常或缺原bytes是觀察環境紅；即使subject0也不能發布完整正式PASS。

每phase原stdout/stderr/stdin保持全量、原exit與exception分欄。外層reaper原primary exit與包裝exit分開；不能把環境75、Python traceback2或compiler非零當產品指定assert1。工具在collector完成後凍結真hash，由新launcher核對，不能此刻填假pin。

正式checkout應是新薄detached F，源自已存在Git objects，原public工作樹不動；精確NativeBuild／quoted include／Python imports所需closure與room_a.scene先列manifest，對F逐bytes核實。所有C/build/temp只在本線指定WS子目錄；TMPDIR固定到該私有路徑，不用root/globalcache或僅剩約28MiB的全域/tmp。統一16MiB stack，記soft/hard，無法設定就環境紅。沿root授的一個secondary correctness槽，所有phase串行；不與性能／完整canvas並行。phase C編譯仍走原NativeBuild，不更改flags、assertions或timeout。

## 磁碟預算與目前不能開跑的原因

已讀舊#346 RAW_INDEX metadata，未讀／hashpayload：603原件合計16,622,515B，其中compile-retention68檔1,052,022B、observed commands354檔304,661B。最大浪費是三份無限定的git ls-files-stage stdout各約4.52MB；新driver只保存精確closure entries，避免重新複製整個repository的巨大index清單。這是收據精確範圍，不刪來源或隱藏命令輸出。

原100MiB guard仍是**最低環境門檻**，不是已證足夠的新預算：新H有513個declaration的多session原流、placed512 references、7ABI閉包及9個helper phase，實際bytes尚未量測。C objects/ELFs原NativeBuild TemporaryDirectory會依原cleanup清理可重建檔；先保全原compile inputs、headers、build logs、binary hash和完整runtime流，不刪已封收據／fixtures／Git objects。每phase結束後再查剩餘空間，若低於原100MiB就不啟下一phase，將未跑項明列，不降低guard。

執行前先由collector準備程式只stat量化：薄source closure S bytes、單phase原NativeBuild最大可重建輸出估B、已留原件R、collector新寫入I與filesystem配置餘量。預算需容納 S+B+R+I，且另外保root指定collector reserve；沒有可辯護上界時先跑collector自驗／靜態準備，不能把100MiB直接當完整14＋9階段會塞得下的保證。歷史W的1MiBretention不能外推為H所有輸出也只有1MiB。

本輪source出版只需小metadata；完整性能原件封包另由storage處理。storage新估43,143,707B既有tar的loose＋push pack就需額外86,287,414B，新memo再加，與本線C原件預算不能共用同一份空間。正式槽和足夠磁碟、collector獨審三者齊備之前不啟動。
