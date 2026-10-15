# PR #237 B1: explicit integrity counters

本輪接手看板步驟 A 的未照顧 PR，回覆 ChatGPT 審查
[6178679029](https://github.com/ZhiQiYang/geometry-axiom/pull/237#issuecomment-6178679029)。
接手前 head `8030d34365d11a0e9974b80d5014203a0c8a517c`；
修後完整受測 head `fa713704aac53b40b46cb0ee4acdcbf38f6b9c59`。

`archive_wait_trace.py` 原本將缺少的 drop/error 補 0，將缺少的
accepted/written 補成檔案筆數，會把遺失內部事件的檔案驗成完整。
現在四項一律明確提供、嚴格非負 JSON 整數；bool、float、字串、null
及其他型別均拒收，不從檔案長度反推計數。原 run ID／marker／request
begin/end／loss／file count 檢查仍保留，失敗仍逐字保存 raw JSONL。
既有正向 fixture 補為五筆完整記錄；新增方法直接使用真正 Writer，
證明其輸出可封存，再逐一缺欄、錯型別、負數與刪掉 release 反測。

## 紅綠與撤修

`b1/contract-control-before.*`：修正 actual0。
`b1/contract-withdrawal.*`：僅將 collector 還原為原 Git blob
`0f70656056e4d010aea3bfce08b234d27f0e46f7`，同一份最終測試源碼
產生 14 個具名誤收 subtest failure，actual1，error/skip 0。
`b1/contract-control-after.*`：還原修正 actual0。
三份 JSON 均有 collector 與測試 SHA256；沒有修改 Writer 或測試來湊紅。

首輪 `before.*` 及較早 `withdrawal.*` 有 18 個 failure，其中 4 個只因
把既有 invalid-trace 強求成 incomplete-or-mixed-trace，並非誤收。
後續只要求既有兩種拒收狀態皆可，14 個真正的誤收仍會紅。
所有原輸出保留，不把首輪 18 個都聲稱為誤收。
`python-all.*` 是收窄分類斷言前 Python20/20，`node-transport.*` Node7/7；
最終測試源碼的 Python20/20 由下面完整 native 再實跑。

## 獨立實際 CLI 比較

`collector-matrix.tar.gz` 保留 30 組完整 input、原/修後 collector 的原始
stdout、stderr、receipt.json、實際複製的 raw JSONL；`matrix.json` 列出退出碼。
真 Writer 五筆完整輸出 actual0，其餘29組修後 actual1；原 collector16組誤收。
包括審查原例：保持合法 begin/end、刪掉中間 release，再省略 accepted/written
會被原版接受，修後拒收。原版 source bytes 也在包內，不改寫歷史檔。
CLI 中 receipt 的 head 是執行 cwd 的 head；原 collector 的身份以原 blob
及獨立 SHA 為準，不能把這個 receipt head 當成原 collector 的來源提交。
每次均逐 byte 核對 raw copy；`collector_matrix.py` 是外部重現腳本原件，
沒有另加到 repo 的可執行測試清單。

## 完整 native

原完整 native 終局 actual0；89 suites、2805 pass／0 fail／1具名允許 Windows GDI skip，Node711/711；wall 879.204秒。
前後固定 head、14989 個追蹤普通檔 SHA 一致（排除 expected），204 個本輪 log 成員逐件核符。
`run_native.py` 是外部捕捉腳本原件；原 run_all 命令未改。
完整命令為 `ulimit -s 16384; python3 -u tests/run_all.py --build --update-expected`。
不帶 only／allow-skip；新增一個測試方法，完整 census 產生 wait trace19→20，
再獨立核對整張 suite map 只有此一差異。原 expected bytes 排版會保留。
`MUTATE_CACHE` 指向本輪開始時不存在的獨立路徑，避免沿用其他來源的舊 cache；
mutation:check 只核現有 ledger 的可攜 freshness，不是重跑所有 C mutants。
本輪沒有 C 產品變更或 C ledger 新增覆蓋。

`native/tracked-before.json.gz`／`tracked-after.json.gz` 是 gzip 保存的原始兩端逐檔 SHA（解壓後 bytes／SHA 在 tracked-endpoint-manifest.json），
唯一排除明示由 census 重寫的 expected；不是連續監看。
`native/binary-final.json` 只提供最終五 binary hash 與 sidecar，未交付 exe bytes，
也不宣稱 binary 前後身份不變（原 build 確實因來源指紋改變而重建）。
`native/native-current-logs.tar.gz` 只收本輪開始之後實際寫入的 log 檔，
逐成員 bytes／SHA 在 native-log-manifest.json，不混入共享目錄的歷史日誌。

## P-119 的未驗部分

B2（P-119 稱 B3）的 canvas 規模 trace overflow／未配對請求仍待原本機
owner 對 `c54324f7c7e2e3552a8d7fe709ec219dcdaeb3ff` 在排他條件下孤立重跑。
這個舊 train head **不含本次 B1 修正**。P-119 的既有六項裁決與後續
舊 canvas 結果不自動延伸到新 head；新整合驗收仍交 Claude／本機工人。
不改原 JSONL、collector 規則或原退出碼，不裁尾、不補事件、不自行排 WSL。
本輪也沒有將 sink 移回業務鎖或自行定義可接受的資料遺失政策。

本輪相對8030只改 collector、既有 test_wait_trace.py、WAIT-TRACE.md、
完整 census 的一筆 expected 與本證據目錄。共享 workflow 本輪未改；
C、ledger、SSOT、白話、正典、BACKLOG、決策與 🔒 行均未改。
本分支未新合目前 main；雲端 native 只證上列固定 PR head，不冒稱最新整合。
GEO-219：無新入口。mutate 無新覆蓋。
未跑 WSL、未合併／關閉 PR、未 force push，維持 draft。
