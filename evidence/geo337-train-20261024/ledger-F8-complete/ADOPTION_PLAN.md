# F9 原帳本採入計畫（尚未執行）

生成來源 F8：75a1e93811a52b69385cbdaf6a09d773ed9052ad。
原帳本：/tmp/geo337-full123-F8-job-20261025/mutants_results.json。
SHA256：0123548b29bf8adbaf3cf896bfffb212134452f2574eaf8ae1d1b663104ead1b。

先決條件：原 CLI/root/outer/exec 皆0；123列/120自然F8 head/3retired；原四階段1/0/0/0保留。獨立逐列原件 peer 與完整封包 peer 真0，完整封包和peer原件先一般推到train evidence。採入時固定最新BEFORE，與遠端完全相同、工作樹及index clean，F8→BEFORE使用 --no-renames -z 確認只有 evidence/。

root只將上述JSON逐byte寫入已追蹤tests/mutants_results.json並在PROGRESS附採入事實。用git add --update限定此兩路徑；檢查cached diff --no-renames -z僅兩檔、實際JSON Gitblob bytes SHA相同，再普通英文commit及push；不得改execution.head/date/verdict。普通推後ls-remote完整相同才稱已推，固定F9。

緊接在F9清除全部MUTATE_*，原python3 -B tests/mutate.py --check，用原c387逐條錄命令/完整stdoutstderr/環境/退出碼；不以外置JSON/check0代替。F8→F9除evidence外只容帳本且必實際變，原裁判/產品hash不變。結果若紅，保存原件並查因，絕不改head湊綠。

新F9 trackedcheck及後續native/browser/專項為實際F9；原帳本生成、R8量測維持F8身份。此計畫不解除exact/B/C/CI、不宣告READY。
