本目錄準備固定 L `43f85313c32410ac01406ab585846bbacafea278` 的架構 CLI 獨立入口。父代理尚未放行；目前未執行 runner、架構 CLI、產品測試或建置。

首稿只檢查 native 的 HEAD 與套件數字，獨立審查指出任意 suite 目錄會讓舊 R2 的同數字結果被錯誤引用。首稿原 bytes 與意見保存在 `首稿/`；這不是測試執行失敗。

修正版固定本輪 native 的 command、啟動時間、工作樹、wrapper／launcher 原碼與啟動原件 hash。正式放行前必須取得完整 native 收據、父 launcher 的真實 wait 結果、前後 L clean 記錄、224 套件核對收據及來源索引。六份具名 JSON／log／unittest.log 必須來自本輪封存，逐件核原來源路徑、mtime、bytes 與 hash，JSON 另核套件檔名與通過／skip／error 欄位。

架構 CLI 命令固定如下；不重產四份 metadata，不重跑 native 內已具名執行的 generic 205／product 18 套件。

```text
env -u CC -u PYTHONOPTIMIZE python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json
```

runner 會保存完整子程序環境與 argv、開始／結束 UTC、真實 raw wait status／CLI exit／外層 exit、stdout／stderr 原件，以及主工作樹前後 HEAD／status、三支工具與四份產物原 bytes 雜湊。它只寫新建的 repo 外輸出目錄，禁止覆寫既有收據。Git status 的 clean 指無追蹤變更及非忽略的未追蹤檔；不是聲稱 ignored 建置產物不存在。

已接入 native 專責封裝器的 `verification.json`／`named-required-suites.json` schema。完整核對收據另須透過 CLI 明示 SHA-256 pin；其 provenance 必須逐項吻合本輪 command、native 收據、launcher 收據、source index、expected、原 run.log 與實跑封裝器的路徑／bytes／hash。224 完成布林保留原生 GDI 具名 skip 與 exit-code-only 分類，不表示每一項都是實際斷言通過。

放行後使用下列命令，把最後一個佔位值換成本輪凍結 `verification.json` 的實際 SHA-256；不得在 native 尚未完成時填入歷史結果。

```text
env -u CC -u PYTHONOPTIMIZE python3 -B /workspace/geo261-evidence/architecture-L-preparation/run_L_architecture_cli.py --root /workspace/geometry-axiom --out /workspace/geo261-evidence/architecture-L-formal-43f85313 --native-dir /workspace/geo261-evidence/native-final --native-launcher /workspace/geo261-evidence/native-final-launcher --native-verification /workspace/geo261-evidence/native-final/verification.json --native-verification-sha256 <本輪正式verification原件SHA256>
```

目前 native 尚未完成，未執行上述命令；缺任何原收據或核對不符都會在 CLI 啟動前失敗。不能把本目錄存在、AST 成功或方法獨審通過當作 L 架構驗收成功。最不確定處仍是本輪 native 與正式架構 CLI 的實際完成結果，須等待原始收據。
