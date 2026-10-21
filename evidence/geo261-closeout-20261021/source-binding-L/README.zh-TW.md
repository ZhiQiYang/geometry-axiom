# 最終 L 的來源綁定

最終帳本提交 **L=`43f85313c32410ac01406ab585846bbacafea278`** 已公開在 `codex/geo261-closeout-20261021`。本輪只讀核對完成，沒有執行產品、編譯、正式 `mutate.py --check`、架構掃描或瀏覽器。主代理已實跑的預設 check、普通 push、遠端查詢原件另保存在本包 `ledger-L-cc-import/`；完整整合驗收仍由其他收據證明。

來源 A 為 `7159530c0e494d3211e6ab1764eb691137211707`。帳本 75 筆 execution 都是在 A 實跑，沒有改標 L，也不宣稱帳本在 L 重產。

## 核對結果

| 核對 | 結果 |
|---|---|
| A 是 L 祖先 | 是；完整鏈為 A → `cd4ac98f44174729fb3a2f1c291c6c258c9a239a` → L |
| 每次提交與整段差異 | 兩次提交各自以及 A→L 總差異均只有 `tests/mutants_results.json`；其餘全部 tracked 路徑沒有差異 |
| 快照檔案聯集 | 1010 個路徑，1009 個原 bytes 相同，唯一變動是帳本；不是「1010 全部同 bytes」 |
| 架構輸入與四產物 | 611 inputs 的 LF 雜湊逐筆符合既有收據；四產物 A=L 原 bytes 相同；未重跑架構掃描 |
| 帳本原 bytes | Git L blob、工作檔、第二輪實跑原檔、匯入 `ledger-blob.stdout` 四者逐位元相同 |
| 帳本 | 78 筆，70 killed／1 crashed／4 equivalent／3 retired；75 execution 全部 A；78 筆 record checksum 正確 |
| 無 execution 的三筆 | M35、M51、M55 均為 retired |
| 突變來源 | 所有非 retired 的 source／include closure／oracle／mutant／tool 雜湊與 A、L 快照均符合 |
| 預設編譯命令 | 57 筆 core execution 的命令字面與 compile hash 均符合未設定 CC 時的 `cc`；不以 cc/gcc 指向同一 binary 作豁免 |
| 正式 check 與公開狀態 | 只讀引用主代理原件：預設 check=0、普通 push=0、遠端查詢=0 且分支精確指向 L；本代理未重跑或重新查網路 |

歷史 L1=`cd4ac98f44174729fb3a2f1c291c6c258c9a239a` 現在隨 L 推送成公開祖先，但仍未採用為最終候選。其 CC=gcc 舊帳本與預設 check=1 的原始證據在 `../source-binding/` 保持凍結；舊文字的「未推送」是當時事實，不回寫為當前狀態。這次 L 保存的是重新在 A、預設 cc 環境實跑的第二輪帳本。

## 精確雜湊

- 新帳本：5,170,287 bytes，SHA-256 `868a80700c9d058e208684631e799a91659e7820b06c31c246b8af96c670a731`。
- 原 A 快照：`10c9476ee9ffa456929a4b334691d8762dc28a071a8c51c3ba8490931e7de214`。
- 新 L 快照：487,107 bytes，`72283a36e47831867884f9682684267eddaf5d208acaf3891a0abeb9b3774455`。
- A→L 比較原 stdout：`e6c1312b8e9853a38b62ff382ae4a901ec0309d791ec628bb954798869cddab5`。
- 快照工具原 bytes：`0640270f504fc0f12398cf15dda289f45dda188b9fa42cf3e32b862ee76a9a48`；與 A 快照使用的工具相同，本包以 `snapshot-command-code.txt` 保存。
- 本次比較工具：`efdfd6c4ed7e7b3e81f8f76a0fefe5b56859d660c6709cc1486461015b2332b3`，`compare-final-L-code.txt`。
- 184 檔 include closure：`872824fc382cb0467591d8df22e375c2e9a6649578b170365246ada795fcce63`。
- core oracle（165 個場景及正式 runner）：`f8222a4ac7ae76339cfb7536634f98e572ecd2bb0d649ce3395d6d452e2fa306`。
- 正式 mutation tool：`24c391b89880b8abc36cf4b7431afd1bb5486982cb9d41a6a0d975ac7c3c6387`。
- 預設 cc compile hash：`38f058ea0801edc120a8f48c296e92c4fb835b6ff3dd6d7db8b266a1b1c2873c`。
- 架構 input closure：`4be326e07260a35b456ef4e8d46f50c28432216f66e45c5afc56d46d5313ce9b`。

四產物位於 `geometry-core/domain-decoupling/`：

| 產物 | A=L 的原始 SHA-256 |
|---|---|
| `product-architecture.json` | `b5dff5b3e2573aac6aa38fa433cb3afa71c2ab1828d34d61aabc26df01bbcbc9` |
| `product-architecture-scan.json` | `a107ce7ceff08edede8b0c3c963837f19518d8d9d66ab6014212025fa212d3a6` |
| `PRODUCT-ARCHITECTURE.md` | `a4fffdc84186b899bf4287ddab4b961fb6d96f02233d52fdc413517a2138a344` |
| `product-architecture-receipt.json` | `804142f06ef1c251cd6c2d30fa7d66e1f04609d5e4e39d439169267869dcdf6e` |

既有架構收據記 333 owned、278 excluded、796 edges、0 diagnostics；本輪核對收據來源與原 bytes，不將這些數字冒稱為在 L 重掃出的結果。mutation 的 bridge oracle 另含 225 個根層 `tests/*.py`、171 個根場景與各突變的正式方法清單；本輪逐個定義比較 oracle hash。

## 實跑命令與退出碼

完整 argv、時間、stdout 雜湊與退出碼在 `commands.json`。兩條只讀工具皆退出 **0**，stderr 為空：

```sh
python -B /workspace/geo261-evidence/source-binding-preparation/snapshot_bindings.py --root /workspace/geometry-axiom --expected-head 43f85313c32410ac01406ab585846bbacafea278
python -B /workspace/geo261-evidence/source-binding-L-preparation/compare-final-L-code.txt --root /workspace/geometry-axiom --snapshot-a /workspace/geo261-evidence/source-binding-preparation/snapshot-A.json --snapshot-l /workspace/geo261-evidence/source-binding-L-preparation/snapshot-L.json --import-dir /workspace/geo261-evidence/ledger-L-cc-import
```

快照的原 stdout 為 `snapshot-L.json`；比較原 stdout 為 `binding-A-L.json`。其 Git 命令及原輸出保存在比較 JSON 內。所有資料都由新路徑產生，沒有覆寫歷史 L1 的快照或比較結果。

主代理原始命令是 `python3 -B tests/mutate.py --check`、`git push origin codex/geo261-closeout-20261021`、`git ls-remote --heads origin refs/heads/codex/geo261-closeout-20261021`，三者均為 0，完整輸出／環境／時間在 `ledger-L-cc-import/`。正式 check 記 stale=0、blocked=0；crashed M20 仍明列與斷言 killed 分開，未改分類。

原比對命令內的絕對路徑是實跑環境，不是假裝可在任意 checkout 直接貼用。封裝後工具改以 `.txt` 保存原 bytes，無執行權限；若重現，須提供原命令對應的 repo、A 快照、L 快照與匯入目錄。比較器還會讀匯入收據所記第二輪原檔，該原檔路徑需還原；其原 bytes 已由本輪四方比對及包內 `ledger-blob.stdout` 保存，不依絕對路徑名稱判定正確。

本輪快照曾先輸出至互動工具回傳，該介面截短長輸出；隨後以相同工具重新唯讀擷取並直接保存完整 stdout，才作為本包原件。兩次皆退出 0，沒有以截短輸出製作成功 JSON。

## 範圍與後續界線

快照驗的是 include closure、正式 oracle、架構 receipt inputs、四產物與帳本的聯集，不是全磁碟／執行中 binary 快照；Git 整段 diff 另證明 A→L 其他 tracked 檔案未改。快照自身只要求 tracked clean，這次比較器另要求沒有非忽略的未追蹤檔案，兩次前後 HEAD 都是 L；忽略檔案不在此保證範圍。

沒有在 L 重產帳本，沒有改 execution.head，沒有重跑架構、任何產品測試或效能量測。本輪也沒有產品突變自證；75 execution 與相應測量／還原證據仍應由原 A 帳本執行證據包提供，不能用來源 hash 核對取代它們。

正式七項整合、Q38、§7、replay、P189 應各自保留在 L 的實際開始／結束 HEAD、原命令與退出碼；本包不預先宣告它們通過。之後 E 若只交付文件，仍須另外核 L→E exact diff 與精確白名單；不能因產品 bytes 相同就稱 E 已實測。最新 PR #288 審查對象是 7dae 的原候選，新 A／L／E 組合仍須交使用者貼回 PR 重新審查。

最不確定的是審查者是否接受「帳本 execution 在 A、完整整合在 L、交付在 E」的明示分層；本包只證明其來源關係，沒有替審查者解除來源阻擋或允許合併。
