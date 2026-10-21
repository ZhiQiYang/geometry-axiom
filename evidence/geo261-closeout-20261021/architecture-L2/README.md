# L2 正式架構 CLI

實跑分支 `codex/geo261-closeout-20261021`，前後完整 HEAD 均為 **`249571fe2477845d5330f6190dad965bf327f43b`**，tracked 工作樹乾淨。2026-10-21 04:14:11.853501Z 至 04:14:17.075852Z，耗時 **5.222361799 秒**。

```text
timeout 900 python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json
```

cwd 為 `/workspace/geometry-axiom`。父程序給全新 TMPDIR／pycache prefix、禁寫 bytecode、16 MiB stack，CC／PYTHONOPTIMIZE 不設定。真正 `waitpid` raw status 與結束碼皆 **0**，stderr 空。完整 argv／環境／工具／manifest／四 metadata／來源前後 hashes 與 stdout 保存於本包。

實際 stdout 顯示 **333 登記來源、796 邊、0 診斷**，132208 bytes，SHA-256 `a107ce7ceff08edede8b0c3c963837f19518d8d9d66ab6014212025fa212d3a6`，逐 bytes 等於已封存 scan。611 inputs 的 raw／LF hashes 與這次新 L2 snapshot 一致，LF closure 為 `2c665544b106ed8b2542425ae3d752843e9cd281b340ab349fe8a3734bc36076`；四 metadata、三裁判、expected JSON 與 ledger 前後均未改變。

四 metadata 仍是 S2 真驗收、A2 提交的產物，receipt sourceBaseHead 維持 `cabe824128be31d0039dc6c94fa3f04cfb722a6b`，沒有回填為 L2 重產。這次是 **L2 的正式 CLI 真跑**，沒有重跑通用 205／產品 18 項測試；它們等待 L2 native 完整 suite 原件，不沿用舊結果宣稱新來源已通過。未新增控制、未改產品或裁判、未做完整 native／browser／Q38／§7 驗收。

來源新快照與 A2→L2 ledger 綁定見新 `source-binding-L2` 包。最大未定項是其餘 L2 完整驗收尚未全部結束，本 CLI 結果不替代那些結果。
