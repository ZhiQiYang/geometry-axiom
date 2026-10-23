# Oracle 新 F 原始／公開證據獨立審查

固定產品 SHA `3d681636902371ecc528b20f51eea33e272581c9`，證據 head `9dfdac7bbded443ff5d9624d1c8fdfa7adc0ccac`，正文 head `0ec402a54c3198eb28c04d503521398fd92c5742`。

獨立唯讀工具真 exit 0，2214 項 metadata／位元組核對全符，findings 為空；這是證據核對數，不是新增產品裁判或重跑測試。原八階段 exits 為 `0,0,0,1,0,0,1,0`，原 driver／outer／top 皆為 0。probe 原 stderr 確有 `Ran 60 tests` 與 `OK`，不是從 AST 宣告數推得執行成功。

C4 baseline／撤回／還原保留原具名 C4NEG bad `8/0/8`，撤回為正常原裁判 exit 1。probe 單方法同為 `0/1/0`；撤回真為 `AssertionError: 2 != 1`、`Ran 1 test`、`FAILED (failures=1)`，沒有把載入、崩潰或 skip 當成牙齒。兩組撤回的 anchor 各精確一處、只有預定 target 的 manifest 變更，還原 bytes 與固定 F 完全相同。

85 個輸入的 raw SHA256、Git blob、mode 逐筆綁固定 F；68 個 fixture 精確覆蓋原 core-probe/fixtures 與 scenes。原 source-before/source-after clean 且同 F，初末 manifests 完全相同。原 cfea/c387/6825/7d84 工具 hash 未改；真 argv 明列 `env -u PYTHONOPTIMIZE`，原 R3 與 16MiB stack 皆保留。這些紀錄不把準備 setup 的 exit 0 當成產品 gate。

公開 Git package 全部 payload 的 bytes/hash 已核，archive 為 1,158,344 bytes，SHA256 `8d43a267def65d3b1a669f9f3a0f40352b27d83c7a63f1aad7a3aca8f34577f4`。所有 regular 成員逐筆對 index、原實體檔案與 Git archive 解碼結果；四個原目錄（driver、outer、top、checkout setup）實際檔案清單也核為完整，不只信任 index。原 command request/result/stdin/stdout/stderr 全檢 hash 與完整 bytes，listed result 與真 result 同一。

普通 publication 的 35 個 Git command 均為 0；原 evidence/body 單親前進、修改只在自身證據 prefix、push 未含 force，獨立 ls-remote 核 remote E/D 同一。正文仍誠實保留 actual/public peer pending 的發布當下狀態，只有一個 current-state matrix，未冒先審過。

範圍限原八階段；不外推真正 native run_probe.sh 全場、歷史 159 個 source mutants、native／六 browser 或全帳本。本輪沒有執行產品測試、編譯、瀏覽器或任何 Git mutation。原 unittest 未持久化的內層 child streams 沒有補造。完整核對及 Git 讀取 command/exit/stdout/stderr/環境在 CHECKS.json 及同目錄 subcommands。

CHECKS.json SHA256 `8707c6c4484d839ac4f680c0d291cf07bee1a8355a6e54303eccffb680f0f59e`。
