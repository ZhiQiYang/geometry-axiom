# P0 原生基準與候選收據

本目錄保留四輪實際執行結果，包含最初失敗；不是幾何核心解耦的驗收，也不是 Claude 的正式七項列車。

| 目錄 | source | 命令（皆先 `ulimit -s 16384`） | exit | pass／fail／skip |
|---|---|---|---:|---|
| `baseline` | `1c80751150d0767ba52509537caf8d5542769ccb` | `python3 -u tests/run_all.py --build` | 1 | 2731／89／1；Node suite 缺裸 python，發現數亦少 6 |
| `baseline-node-python` | 同上 | `python3 -u tests/run_all.py --build --only node:tests-js` | 0 | 704／0／0；私有 PATH 補 python3 別名 |
| `baseline-full-python` | 同上 | `python3 -u tests/run_all.py --build` | 0 | 2826／0／1；完整 88 suites |
| `candidate-17a25e92` | `17a25e92c75e8c89063e36ca329729980d8ea6a9` | `python3 -u tests/run_all.py --build --update-expected` | 0 | 2855／0／1；完整 89 suites |

唯一 skip 是具名 Windows GDI harness 測試，在 WSL 不適用；不是 pass。counted values 混合 unit tests、原生場景與 JavaScript assertions，不是端到端情境數。其餘 6 個 exit-only suites 另見逐項總表。

每輪都在固定 source 的 Linux checkout 中，以私有 mount／network namespace、私有 `/tmp` 與 loopback 執行。補別名只改該私有環境，不改 repository 或使用者服務。各 `summary.json` 記工具版本、UTC 起訖、實際啟動命令、來源狀態、來源清冊與 aggregate log 雜湊；`run_all.log` 和 `exit.txt` 是原始輸出。後續僅補證據／手冊的提交不冒稱已在新的 source SHA 重跑。

另保留最初失敗與單一 suite 復測的完整 `run_all-logs/node_tests-js.log`，以便核對環境原因及 704 項恢復：

- 初次 log SHA-256：`5686d4b9c3a6e3bb478096e95f104b9a83f8c3d6bdecc9ce8658f2a5f7be9a73`。
- 復測 log SHA-256：`6ed1c18bec29c2d2cfe34c52178ca6ac2c771b226361a7955d70e037f5e14442`。

候選的新增提案 suite 原始資料是 `run_all-logs/py_test_domain_decoupling_proposal.unittest.log` 與 `run_all-logs/py_test_domain_decoupling_proposal.json`：29／29、0 failures、0 skips。基準及候選的編譯指紋 sidecars 也隨附。完整 tracked-file 清冊與其他 per-suite logs 保留於原始外部證據路徑；其雜湊在 summary，可按相同 source commit 重建核對。

## expected counts 沒有被重寫成較小的數字

候選保存了基準及原 expected bytes、再生 expected bytes、parsed copies、實際文字 diff 與兩份比較收據。獨立可核對：

1. 原 88 個 suite entries 完全不變，只增加 `py:test_domain_decoupling_proposal` 的 29 tests。
2. 再生 JSON 與候選原 JSON 全等；2856 counted、83 counted suites、6 exit-only suites。
3. 再生檔只有排版改變。在語意全等後才回復原 bytes，並重新核對全部 14580 個 tracked 檔；前後清冊 hash 完全相同、status 皆空。
4. run_all、expected comparison、tracked source comparison、combined 的退出碼都為 0；任一步失敗不能宣稱候選通過。

沒有執行六個瀏覽器 job，沒有全量重產原生 mutation ledger，基準也沒有 oracle 目錄可跑 selftest。aggregate 內的 mutation check 只驗既有帳本新鮮度。上述後續工作仍在 GEO-261 的實作／正式驗收範圍內。
