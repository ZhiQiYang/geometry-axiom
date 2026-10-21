固定分支 `codex/geo261-closeout-20261021`、完整 L `43f85313c32410ac01406ab585846bbacafea278` 的架構 CLI 已於本輪實際通過，CLI／外層 exit code 與 raw wait status 均為 0。

實際命令：

```text
env -u CC -u PYTHONOPTIMIZE python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json
```

cwd 為 `/workspace/geometry-axiom`。開始時間 `2026-10-21T00:14:37.303397+00:00`，結束 `2026-10-21T00:14:42.765625+00:00`，耗時 `5.462242823999986` 秒。`stdout.json` 原件為 132,208 bytes，SHA-256 `a107ce7ceff08edede8b0c3c963837f19518d8d9d66ab6014212025fa212d3a6`，與已提交 scan 完全同 bytes；stderr 空。結果是 333 個來源、796 條依賴邊、0 項診斷、6 個依既有契約信任而未解析的來源。

runner 為已獨立審查的 `6f359273e6a38c80ab679c677dd1bd39a235dad2ef2008954a9f9070eb6f6164` 原 bytes，沒有在正式執行前放寬綁定。前後 HEAD 都是 L，工作樹 clean，三支工具與四份 metadata 原 bytes 不變。完整 child 環境在 `environment.json`，原 argv、真實 wait、時間、原 stdout／stderr 雜湊在 `receipt.json`。runner 收據 SHA-256 為 `2dd6aceeda61dc20b3624802e34ba73b27f31fd0511155737d7370e31abe4649`。

generic 205／product 18 套件在本輪 L native 已實際執行，全部通過、skip 0；這次沒有重跑。`native-references/` 保留這六份具名 JSON／log／unittest.log 原件，以及本輪 command、兩層執行器、真實 wait、完整 native 核對與原始輸出的引用。正式 native verification SHA-256 為 `854331066a034b08c85ffebb4257f16a576933b37b89ac7ed49b2af6ec2e4af5`；完整 224 suite 為 5175 pass／0 fail／1 個既有允許的 GDI skip，另保留 exit-code-only 分類，不能稱 5176 全部斷言通過。

native 第一版衍生封裝器的正規表示式曾跨行吞掉表列，該次外部解析 exit 1 與原件保存在 native 證據的 `packaging-attempt1/`。本次綁定的是修正後實跑封裝器 `6be5664f840d7a67d008f3c771ca2d8d644b2c7aa3f15550829333c0973f7831`；原 native 測試與 raw 沒有重跑或改寫。準備期複核所記的舊封裝器 hash 僅屬當時來源，不能代替此實跑 hash。

另外的只讀 `verify_cli_inventory.py` 結束碼為 0：既有 611 項 input 的 raw bytes、LF digest、Git blob 都與 L 及已凍結的 L 快照一致；四份 metadata 亦一致。closure 為 `4be326e07260a35b456ef4e8d46f50c28432216f66e45c5afc56d46d5313ce9b`，分類維持 333 owned／278 excluded。完整逐檔記錄在 `inventory-binding.json`。

本次沒有重產四份 metadata，沒有改其歷史 sourceBaseHead `ab6869b86a4ad82345359b72397fc055280d8308`，沒有把先前 execution 改稱在 L 執行。新的 L CLI 收據和 native 的 205／18 原件才是本輪實測。沒有新增突變控制；架構刷新各輪的既有負控制仍保留在歷史 architecture 證據中，不能稱本次重新執行。

本收據只涵蓋架構 CLI 與上述來源綁定，不替 Q38、§7、P-189 或其他整合項目宣告完成。剩餘不確定性屬尚在分別驗收的項目及 PR 新候選的再審結論。
