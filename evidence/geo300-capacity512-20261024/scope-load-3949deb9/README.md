# 真512載入：261.84秒，尚非整套H7

Execution `3949deb9e565a9e5aeca5bc475ec646e77cc6546`。命令 `TMPDIR=/dev/shm/pr348-scope-512-load-temp python3 -B /dev/shm/pr348-scope-512-load.py`；原O0分離K/W/H建置、16MiB stack、600秒。23:55:05Z開始準備，23:59:33Z完成；產品子程序261.840563475秒、exit0、timeout=false、wait4 RSS222088KiB。原H7生成的512 single場景，loadfile/dump/objects/references 真四回覆，再呼叫原 assert_placed_geometry 驗512完整已放置，exit0。

完整stdout SHA256 `47da66d3264fbe943e01e9085d26e73f4ad7317de7e1b41d48d64fd6f4b6c784`，與舊F2/C512load相同，stderr空。ELF/build log/fixture/input/output/測量腳本均在RAW。沒有選樣或追加抽樣；此為單個512 load診斷，不冒canonical replay/history/整套H7原1200秒已過。

持久化工具前置：workspace只剩233472bytes，小於原400KiB文字預算，未刪未知快取。沿普通Git流程把完成checkpoint推自己的receipts branch，再從GitHub git/blob API讀回完整bytes核對；/tmp原生64MiB reserve、SHM發布64MiB不變，未改mount/quota。v5原Git缺歷史blob失敗在test啟動前，保留原錯誤；v6沿既有write-tree --missing-ok和commit-tree保留未展開歷史樹。原7支preview/history smoke1test exit0，14.73545秒，遠端 `a02a7ddc368786534aca94a54a7f72dc2f2ed1f3`。工具smoke不算512驗收。

正式PR產品仍F2/C；3949仍獨立候選，未採入。接下來小範圍H/K省工有新SHA，不能把本結果改標新source。來源鏈與完整ledger/census/architecture/native/browser仍未完成。
