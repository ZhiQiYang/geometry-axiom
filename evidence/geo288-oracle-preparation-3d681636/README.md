# F3d oracle 八階段準備：未執行

產品來源固定 `3d681636902371ecc528b20f51eea33e272581c9`。此資料只做Git／AST／hash盤點，沒有建立checkout、clone、build、Chrome或測試。所有八phase仍UNRUN，準備collector exit0不代表oracle通過。

`REQUEST.json`已列真完整SHA、精確future argv及獨立tiny sparse worktree步驟；`SPARSE_PATTERNS.txt`只取85個真正輸入與3個本地規則檔。預定checkout `/workspace/geo288-oracle-work-3d681636`，輸出 `/tmp/g288o-3d681636`，兩者準備時均不存在。root在grid/native＋P52窗口後明示slot前，不執行任何setup或proof命令。

85個原輸入含oracle八檔、PROPOSAL、決策佇列、probe七檔與 `core-probe/{fixtures,scenes}` 的68個tracked fixture/scenes；Git mode/blob逐筆與F13相同，各檔SHA256也保存在BINDING/原receipt。這只證輸入身份，仍須在同一F3d執行全部原phase，不能繼承舊綠代替。

driver保持原凍結 `cfea72a0e8dbe94b0c2f08338654e4052aa88e9bf308523689f9c2860a7ba64c`，capture保持c387，outer保持68256d90。原C4與probe撤回anchor各一處；probe AST方法總數60，**不是已實跑Ran60**。原8phase預期 `0/0/0/1/0/0/1/0`：quick、完整probe、C4三態、probe-core-limit單方法三態。原斷言、精確正常failure、golden、正式時限與全source before/after守門不改，不write-expected、不重產golden或帳本、不加Node/Chrome/編譯裁判。

driver自己持原R3排他鎖，outer不雙鎖；16MiB stack與原c387完整streams照原工具。紅燈仍收齊各phase，不讓crash/import error/watchdog/skip冒反證。partial probe含fake-core控制，不冒真正native run_probe.sh全場或歷史159source mutants。

這個分支只由oracle owner寫自己的準備／收據，整合分支由root負責。PR正文分列產品F與evidence head，各動態gate明標未跑；後續原same-F streams另交對抗審。
