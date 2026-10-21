# 未採用的歷史 L1：來源相同，預設編譯指令驗收失敗

本機帳本提交 L1=`cd4ac98f44174729fb3a2f1c291c6c258c9a239a`，父節點 A=`7159530c0e494d3211e6ab1764eb691137211707`。分支 `codex/geo261-closeout-20261021`。主代理確認 L1 未推送、未採用為最終整合來源；本代理沒有對遠端查詢。後續將在原 A 以預設 cc 完整重產，保留 L1 歷史，新的 L 以 L1 為 parent。最終 L 的來源綁定與全部整合驗收仍未完成。

`snapshot-L.json` 名稱產生於 L1 失敗發現前；其 headBefore/headAfter 均明確為上述 L1，不是後續最終 L。原 bytes 保留，不改寫快照內容或 ledger execution.head。`binding-L1.json` 明列歷史／未採用狀態。

## 已完成的只讀來源核對

- snapshot 工具實跑結束碼 0；A→L1 比較工具結束碼 0。它們沒有執行 mutate.py --check、測試、編譯或架構 gate。
- L1 的直接 parent 精確為 A；全 Git 差異唯一 `M tests/mutants_results.json`。排除此檔的 `git diff --exit-code A L1` 為 0。
- 快照聯集集合為 1,010 路徑，**1,009 檔原 bytes／Git blob 相同，唯一變動是帳本**。不能聲稱 1,010 檔全部 bytes 相同。
- mutation source／oracle／tool／definition 快照相同；既有 611 架構 inputs、input closure 與四份 metadata 均相同。架構 counts 是既有收據值，本次沒有重掃圖。
- L1 Git 帳本 blob、工作樹帳本與 A 的 gcc 完整重產輸出逐 bytes 相等：5,170,404 bytes，SHA-256 `1b8fc87eb83ac5fd5af0589aa48795aa868380d9d5ae35b4c1a8bf7af2175c7d`。
- 帳本內 78 筆＝70 killed、1 crashed、4 equivalent、3 retired；78 record checksums 正確。75 execution.head 全為 A，逐筆 source／closure／oracle／mutant／tool hash 符合快照；M35、M51、M55 是無 execution 的 retired。這是保存內容與來源核對，不是預設環境的有效 verdict。
- 比較前後 HEAD 均 L1、工作樹無非忽略變更；`git diff --check` 為 0。獨立代理 p52_review 另以唯讀 Git／JSON 重算確認上述範圍，結束碼 0。

## 主代理實跑的失敗與原因

主代理在 L1、CC 未設定的環境，執行 `python3 -B tests/mutate.py --check`，實際 exit **1**。原件在外部 `../ledger-L-import/L-check.stdout`、`L-check.stderr`、`L-check.exit-code` 與 `check-and-push.json`；本代理只讀，不寫入該目錄。主代理確認停止寫入後，整個目錄逐 bytes 封裝於本證據包的 `ledger-L1-import/`。其 `remote-after-rejected-check.stdout` 與 `L1-未採用狀態.json` 保存主代理查到的遠端仍 A、未執行 push 的證據；這不是本代理另查遠端。

有效摘要為 killed 18、stale 57、retired 3；57 筆 core 都明示 `execution receipt invalid: compile command changed`。帳本原存 70/1/4/3 沒有被覆寫；`--check` 只讀產生有效判讀。

正式 `tests/mutate.py:700–704` 取 `os.environ.get('CC', 'cc')` 作 argv 首項；`:693–696` 以完整命令 JSON 計算 compile hash。`:1014–1019` 對同 platform 比較保存命令與現行命令及 hash，沒有將 cc/gcc alias 正規化。兩者即使解析為同一 `/usr/bin/x86_64-linux-gnu-gcc-14`，仍不符合這項字面契約：

| 環境 | argv 首項 | compile SHA-256 |
| --- | --- | --- |
| CC 未設定 | cc | `38f058ea0801edc120a8f48c296e92c4fb835b6ff3dd6d7db8b266a1b1c2873c` |
| CC=gcc | gcc | `e87acf5cb27ff17c66fef1d6219c4f31ed95a852b4fc6e3d13840c33db8eeaee` |

`.github/workflows/integration-tests.yml:16–32` 的 native job 沒有 CC 覆寫，直接執行 `python3 tests/run_all.py --build`；`tests/run_all.py:512–513` 會呼叫正式 mutation:check，`:547–555` 保留非 GEOMETRY 的一般環境。故欲驗現有 workflow 的預設路徑，應以 CC 未設定的 cc 重產與核對，不應僅為帳本通過改 CI 或回填 compile receipt。57 筆是 60 core 減 3 retired；18 bridge 的獨立執行收據規則不同。

`compile-context-code.txt` 使用正式只讀函式重現兩個 hash，實跑輸出為 `compile-context.json`，結束碼 0。它不重跑正式 check，不能取代主代理的 exit 1 原件。p52_review 也獨立讀取上述條文，確認此判斷符合既有契約。

最不確定的是後續預設 cc 全量重產與同一最終 L 的整合結果；目前不預填。來源 bytes 相同不能消除編譯指令失配，L1 的來源核對成功也不能被引用為最終驗收通過。
