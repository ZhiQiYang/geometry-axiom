# PR #237: main integration after B1 acceptance

回覆 [6181726787](https://github.com/ZhiQiYang/geometry-axiom/pull/237#issuecomment-6181726787)。
該審查已解除 collector B1，保留 B2／最終整合阻擋。

## 來源與唯一衝突

以一般 merge 承接 main `839063b9eecbd3592f48cab5ea74f306cacc5fa3`，
第一父提交為原交付 `879ceee4931e67d0d58400d3f573a35c12fd0591`，
merge／受測提交 `3642e67d974f4aa712f174a4483e4b5bc3589667`。
沒有 rebase／force push，沒有修改 ops/agent-board。
Git merge-tree 與實際 merge 都只在 `tests/run_all.expected.json` 衝突。

`expected-base.json`、`expected-ours.json`、`expected-main.json`
保存三方獨立解析資料；`expected-resolution.json` 列出判斷與結果。
本案沒有同一 suite 兩側都新增的數字衝突，只需保留兩側變更：

- main 的所有 suite 數量與鍵均保留。
- `node:tests-js` 為 main704＋本線7＝711。
- 本線 `py:test_wait_trace` 保留20。
- 與 main 比對，整張 map 唯一差異就是上述兩項；與先前 PR 相比，
  新核心見證等 main 增量也全部保留。

C、mutation ledger、SSOT、白話、正典、BACKLOG、決策佇列、mutate 工具、
核心 integrity 測試均與 main 逐 byte 一致，只經一般 merge 承接，
沒有作者另改公理、政策或重產帳本。collector／Writer／serve／workflow
及既有本線測試逐 byte 等於879ceee，沒有再修改 B1 或資料遺失政策。
`source-audit.json` 記錄各路徑／來源身份。

## 雲端 native（非正式 WSL）

原完整 native actual0；89 suites、2852 pass／0 fail／1具名允許Windows GDI skip，Node711/711，wall 1073.508秒。
原41題及等待追蹤20題全過。前後固定 head、15083個追蹤普通檔案SHA全同，包含expected。
本輪204個log成員逐件bytes／SHA核符。
完整命令 `ulimit -s 16384; python3 -u tests/run_all.py --build`，
沒有 only／allow-skip／update-expected，不生成或調整測試期望。
`native/expected-before.json` 與 `expected-after.json` 必須完全相同。
原 build 按指紋重建與 main 對應的 binaries，沒有沿用前一輪79412a85的舊 C。
`MUTATE_CACHE` 是開跑時不存在的獨立路徑；mutation:check 只核目前 main
ledger 的可攜 freshness，沒有把它當作全體 C mutant 重跑。

`native/tracked-before.json.gz`／`tracked-after.json.gz` 保存測試兩端
所有追蹤普通檔案的 SHA（這次連 expected 也不排除），不是連續監控。
解壓後 bytes／SHA 在 tracked-endpoint-manifest.json。
`native/native-current-logs.tar.gz` 只收開跑後實際寫入的日誌，
完整逐成員 bytes／SHA 在 native-log-manifest.json。
binary-final.json 只有最終五 binary 的 SHA／sidecar，沒有交付 exe bytes，
也沒有宣稱前後 binary 身份相同。

正典 `sync_axiom_reader.py --check` actual0，沒有原位重產或改閱讀器。
原41題另由上面的完整 native 實跑；其 stdout／JSON 在 native 包內。

## 收據與提交對照

| 執行 | 實際受測 SHA | 收據與範圍 |
| --- | --- | --- |
| 本輪雲端 native | 3642e67d974f4aa712f174a4483e4b5bc3589667 | 本目錄 native/；只證合流來源的非瀏覽器 registry |
| collector B1 紅綠／撤修 | fa713704aac53b40b46cb0ee4acdcbf38f6b9c59 對應的最終測試與 collector hashes | 前目錄 wait-trace-b1-counters-20261015；本輪產品 bytes 相同，但舊 native 不算本輪整合 native |
| 舊第15班六項裁決及待重跑 canvas | c54324f7c7e2e3552a8d7fe709ec219dcdaeb3ff | P-119；不含本次 B1，不能作本輪整合收據 |
| 交付提交 | 由最終 PR 正文與交付留言列出 | 3642e67d 之後只新增本證據目錄；正式七項仍待在新的固定整合 SHA 實跑 |

| 本輪整合 head 的正式 WSL job | 結果 | canvas trace receipt |
| --- | --- | --- |
| native | 未驗；雲端結果不能冒作 WSL | 不適用 |
| assembly | 未驗 | 不適用 |
| documents | 未驗 | 不適用 |
| grid | 未驗 | 不適用 |
| canvas | 未驗 | 本輪未執行完整 canvas，沒有本輪正式 trace receipt |
| space | 未驗 | 不適用 |
| timber | 未驗 | 不適用 |

P-119 的本機工作順序與原 c543 孤立 canvas 不變；本雲端不排 WSL。
原 c543 的結果不自動延伸到這次 B1 修正及新整合 head。
若完整 canvas 仍 drop／write error／unfinished／counts 不符，
必須定位容量／收尾問題；不放寬 collector，不刪尾或補事件。
PR 維持 draft，來源可合併不代表正式七項完成或已准合併。

## 差異空白檢查的原件

最初對整張 PR 做 diff --check actual2，指出既有歷史 raw log 的空白行；
外部 preflight 的 assert 因此中止，外層 shell 仍啟動獨立 native 捕捉。
不是 native 失敗，也沒有中斷／重開 native 或在測試中改來源。
author-diff-check.stdout 保留這份輸出。
對第一父到 merge 的整包 diff --check 同樣 actual2，指向 main 決策佇列
使用者原話的尾空白；與 main 逐 byte 一致，未清洗受保護原文。
限定產品／測試／workflow 的 PR diff --check actual0，
唯一作者合流解法 expected 的 diff --check actual0。
preflight.json 逐項列出實際退出碼，沒有把整包 diff --check 寫成通過。

GEO-219：無新入口。mutate 無新覆蓋。本輪未跑 WSL、未合併 PR、
未 force push、未關 PR／issue、未改設定或共享 runner。
