# L3 架構 CLI 實跑

實際 checkout／前後 HEAD 為 `6589248c9a94bdf0460d8f84dd1610e51048188b`，分支 `codex/geo261-closeout-20261021`。正式命令為 `timeout 900 python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`；完整 Python 絕對路徑、argv、cwd、取消 CC／PYTHONOPTIMIZE、16 MiB 堆疊與新快取／暫存環境均在原 `command.json`、`environment.json`。

2026-10-21 05:42:44.179545+00:00 至 05:42:49.107066+00:00，真 wait status 0、exit 0，耗時 4.927537656003551 秒。stdout 完整保留為 `stdout.json`：333 owned sources、796 edges、0 diagnostics，SHA256 `a107ce7ceff08edede8b0c3c963837f19518d8d9d66ab6014212025fa212d3a6`，逐 bytes 等於既存 scan。stderr 為真空檔。

前後 HEAD 與 tracked clean 都符合；611 架構 inputs、四 metadata、三個架構入口／測試檔、expected 與帳本的原 hash 均保留。四 metadata 的原 sourceBaseHead 仍是 S2 `cabe824128be31d0039dc6c94fa3f04cfb722a6b`，沒有重生、回填日期或來源 SHA。完整 611 清單與 Git raw／LF 綁定在相鄰 `../source-binding-L3/`。

本程序沒有重跑 generic 205／product 18。封包時本輪 L3 native 尚未完成；後續須由該輪具名 suite 原件建立獨立引用附錄，不能用舊 L2 或相同題數替代。這段記錄保持當時事實，不以後續成功回寫原收據。

本輪是正式架構 CLI 實跑及不變來源核對；沒有新增 manifest、突變或負控制。既有 S2→A2 架構刷新與 WoodContactOrder 控制證據另有凍結包。本 CLI 綠燈不代表全產品驗收或 PR 複審已完成。
