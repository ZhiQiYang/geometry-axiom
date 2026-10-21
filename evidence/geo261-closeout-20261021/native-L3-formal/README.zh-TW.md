L3 native 完整正式驗收通過，來源固定為 6589248c9a94bdf0460d8f84dd1610e51048188b。本輪在 detached 工作樹 /workspace/geo261-native-l3-6589248c9a94-20261021 執行；來源前後皆該 SHA 且 clean，未修改或提交產品／tests。

正式命令為 timeout 2100 python3 tests/run_all.py --build，含 build 的2100秒上限與16 MiB stack不變。父環境以 env -u 移除 CC、PYTHONOPTIMIZE、GEOMETRY_ENGINEERING_BRIDGE、GEOMETRY_MODEL_BASE、GEOMETRY_TEST_BRIDGE、GEOMETRY_TEST_CORE、GEOMETRY_TEST_ENGINEERING_JSON、GEOMETRY_TEST_GDI_HARNESS、GEOMETRY_TEST_PF3_ALGORITHM。wrapper設定 PYTHONDONTWRITEBYTECODE=1、LANG=C.UTF-8、LC_ALL=C.UTF-8、TMPDIR=/tmp/geo261-native-l3-6589248c9a94-20261021。完整真實外層 argv及-c原碼在 launcher/dispatch-command.json、launcher/launcher-command.json、command.json與external-code-receipts/instance.json；沒有用CC=gcc掩蓋預設cc字面契約。run_all原suite輸出仍固定於/tmp/geometry-tests/run_all-logs，TMPDIR不當成隔離該位置的證明。

開始 2026-10-21T05:49:55.452245Z，結束 2026-10-21T06:20:25.133869Z，經過1829.681555593秒。224個suite及188份Python結果完整，計數5188＝5187pass／0fail／1個具名合法GDI skip；expected mismatches0、missing logs0、額外skip0。timeout主子程序、wrapper、launcher及工具session真退出碼均0；session75129、工具chunk b139d1。tool-observation.json及finish-native-tool-observation.json保留實際工具回應的事後逐欄轉錄，明示不是transport自動日誌；完成收集器工具chunk513441亦0。

600份完整suite raw共296690 bytes，已逐bytes/hash/mtime核對suite-log-source-index.json；沒有刪空log或將exit-only入口虛構成test數。唯一skip為 test_gdi_contract.GdiContract.test_confirmed_failures_release_real_resources，理由 requires compiled Windows GDI contract harness；POSIX無Windows GDI資源，這一題不是pass。

同L3具名結果：py:test_architecture_contract為205/205、py:test_product_architecture為18/18、py:test_geo261_model_base_replay為6/6，均無fail/skip。mutation:check只代表inventory freshness的exit0；原total/skipped為null、passed/failed為'-'，note明載exit0，不宣稱本輪重跑全部ledger突變。其餘六個exit-only入口保留原ok/exit語義。native內既有測試與控制按原suite完整執行；Q38、controls、整卡及公理版本的獨立突變裁判另有正式入口，不能由native綠外推。

初建六個POSIX binary及六個sidecar共12件的原索引、fresh結果及首個[1/224]前後紀錄均保留；結束再次保存12件，原索引核bytes/hash/mtime與初建一致，兩次tests/binaries.py status皆exit0。這次封裝只從native-binary-preservation的initial-build/final-build已保存原件複製各六個sidecar到對應fingerprints目錄，逐bytes/hash/mtime相同；沒有讀正在供Q38用的global，也沒有拷binary進包或給browser。初終相符只代表採樣點，不宣稱期間從未暫寫。

外層subreaper只回收自己的子樹，主timeout退出碼獨立保留。固定wrapper的wait迴圈只有遇ChildProcessError/ECHILD才完成；本輪正式完成收據已落盤，共11筆回收事件、主事件raw/code0，沒有需要發額外cleanup signal的收養子程序。父launcher真wait wrapper0、工具真0，詳cleanup-verification.json與原reaped紀錄；不以/proc PID不可見冒充清理證明，也不宣稱主機沒有其他程序。

L3前置正式exit0，沒有L2的前置拒讀或PID探針失敗。原四個環境PID1/2/205/258的UID四值、start ticks、PPid、comm及完整cmdline由本輪重新比對；其fd/exe仍未能讀取，其他未解釋PermissionError仍拒絕。歷史身分原件及L2封包工具只作來源參照，不改標成本輪採樣或失敗。

本包只證native與其內含具名suite。封包時Q38與canvas由其他生命週期管理，本包沒有它們的最終結果，也不外推其餘browser、獨立gates或P189。最大未確定處是這些獨立正式入口的同L3結果；Windows GDI唯一skip也仍未在本機驗到。請使用者在 PR #288 更新同L3 native已通過與上述未驗界線，其他項目依各自正式收據另列；本包不提出合併請求。

external-code-receipts中的.txt是實際外部調度／前置／收集／封裝程式原bytes收據，並非新增正式產品工具；instance及原路徑/hash映射一併保存。包內無binary、.py/.js或execute bits。raw-source-index.json列每件copy的原路徑與hash/mtime，artifact-index.json列本包除自身外全部hash。原verification、named-required-suites、source-index、600raw及既有收據逐byte保留；最終bundle是此包逐byte副本，copy核對另放sibling native-L3-formal-appendix。
