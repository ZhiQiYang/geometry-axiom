# Recorder fidelity v5 草稿：只修外部錄製器

原 v4 及 U=`ca7838e0f4950452b9befcf40899d606db9b81fa` 的全部原收據保留。U N64/main=1.429347781620555、原compare1與其他原紅沒有被這份工具改判。沒有執行產品、C、瀏覽器或新效能樣本。

`tools-v5/` 僅改 `geo323_record.py` 與外層 `run.py` 的兩行 perf 呼叫包覆。`verify_linux.py`、`profile_linux.py`、`mini_gen.py`、`reap_children.py` 逐byte等原v4。原36樣本、N、順序、門檻、600秒、stack函式與 `perf_counter()` 原位置不動；原stage清單仍八項。須用全新OUT，不能覆寫或續用原v4的同OUT。

`Recorder.run` 直接呼叫匯入時保存的原 `subprocess.run`，以原 `capture_output=True` 取得PIPE，不另外指定stdout/stderr檔案、DEVNULL stdin或process session/group。caller的argv、cwd、input、明示env、preexec_fn、timeout與check原值直接傳入；未明示env仍沿既有驗收器的受控self.env。普通呼叫返回同一個原CompletedProcess，原例外也保同一物件。既有純儲存選項`read_output=False`仍返回空stdout/stderr，完整原bytes另保，不能當缺件豁免。

性能stage在原 `perf()` 外包 `defer_flush()`，所有request/stdin/兩輸出/hash/索引的序列化與落盤都在原perf返回後的finally執行，原assert或timeout也會嘗試flush。每sample只留下小記憶體紀錄、環境選取與時間點；仍有非零Python觀察開銷，沒有假稱零成本。不在sample內讀／stat／hash scene、掃source或另建fixture；原scene與stdin準備流程不改。

非bytes型的無效input仍先交原subprocess裁定，不能讓輸入快照轉換提早取代原例外；不能保全的輸入另標錄製失敗。

記錄失敗會列`recording_errors`／`RECORDING_ERRORS.json`並向stderr明報，不能標完整。若原呼叫同時失敗，保原例外而不讓錄製錯誤蓋掉；原呼叫成功但flush失敗則外層紅。失敗的pending原bytes留記憶體，不自動覆寫重試。SIGKILL或整個程序意外消失仍可能使尚未flush的記憶體資料無法回收，必列缺件，不能從部分索引推通過。

原stdlib TimeoutExpired沒有暴露kill/reap後的真OS退出碼，所以新收據如實留null，不猜-9或124；只保原例外暴露的partial bytes，不冒完整kill後輸出。原整體run.py/subreaper仍保，recorder不再自行添加process group。所有失敗與非零語意由原stdlib決定。

自驗為純Python synthetic：48個契約檢查，涵蓋真PIPE／繼承stdin／相同session、binary大輸出、非零、原CP／例外identity、原600參數、deferred無hash/JSON/file-read/stat/source-scan、assert後flush，以及雙重失敗仍保原例外。synthetic sleeping child只測原timeout契約，不是產品耗時樣本，也沒有性能通過閾值。

兩份隔離副本各做0/1/0：撤回PIPE改成v4式普通檔案目的地，真child的PIPE契約assert紅；撤回run.py的defer包覆，原perf callback內不得出現錄製落盤的assert紅。全部原工具不動；這些是外部工具反證，不算產品mutation kill。原完整stdout/stderr/退出碼見`contract-r3-launch/`與`counterfactuals-r2/`。

工具尚待train獨立對抗審；不得自行用它抽新產品樣本。原v4 source_role掃argv中base字串的啟發式保留不改，原欄仍須配合明確acceptance SHA、inner與Git guards解讀。
