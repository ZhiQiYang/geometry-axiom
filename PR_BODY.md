這份補丁為核心 K 與矩形格網模板加入隔離編譯及功能見證。`geometry_woodworking` 與 `geometry_app` 即使確實可匯入也必須被拒絕；K 引入已安裝模板的 quoted／angle literal header 都會被原層界守門攔下。矩形格網的實際功能與核心整除反證一併保留。

本輪 current-state 唯一矩陣：

| 項目 | 目前身份或結果 |
| --- | --- |
| Current source SHA | `4d3a17c306cad42057589c5cfd964f1c32b755c4`，已一般 push 並 ls-remote 核同 |
| 實際正式執行 SHA | `bfbab207a92a809fca50fefcefb3fa4b2af05ea9`；本輪 13／七階段原始結果固定在此，未改標新 head |
| Evidence head | `d45dbbc3e96c85e6d1caa629f6abafdfd62c5974`，已一般 push 並 ls-remote 核同；只新增 `evidence/kernel-without-woodworking-bfbab207/` |
| 最新普通合流 | parents evidence `d45dbbc3e96c85e6d1caa629f6abafdfd62c5974`、root 列車 `9a05ae785846446ce8982379b4cb66f4ffde6e5c`；原 bfb 受測薄 source／raw 保持不動 |
| 產品差異 | 對最新 root `9a05ae785846446ce8982379b4cb66f4ffde6e5c` 僅 `tests/test_rectangular_template.py` 與 expected 方法數 11→13；無公理、決策或產品實作更改 |
| 來源檢查 | bfb 受驗前後均 clean、HEAD 固定；新合流 SHA 的 11 個受驗 inputs bytes/hash 仍逐檔完全等 bfb；leaf SHA256 `e948fb78e81a075875a45041009fb379e58d783c8d6b579cd9fa2f81cd40910e` 未變；11 個輸入逐檔綁定 Git blob；兩產品檔 diff-check exit 0 |
| 歷史原件空白檢查 | 全 diff-check exit 2，僅舊 evidence/CANDIDATE.patch 六行 patch-context 空白；保留原件，不計作正式測試結果 |
| 正式 13 方法 | 在實際執行 bfb SHA 的原入口 exit 0，真 `Ran 13 tests in 0.910s`、`OK`、零 skip |
| 原七階段反證 | 在實際執行 bfb SHA 的真退出碼 `0/1/0/1/0/1/0`，外層 exit 0、原 driver exit 0；三個撤回階段均為具名正常 AssertionError，還原階段均綠 |
| 反證內容 | 可匯入的 woodworking sentinel 撤回攔截後紅；K→模板 quoted／angle header 都真編譯執行 0 後被層界拒絕 1；撤回層界或 angle parser 後分別有 2／1 個正常斷言紅；核心格網整除另保 `0/1/0` |
| 獨立對抗審查 | 合流靜審 116 checks／0；正式 actual peer 530 checks／0，SHA256 `68fbc441248d9bb5acc906c7b682f6f95b8b4143d5b1174c69c035acca633f85`，全文在原件包內 |
| 完整原件 | `nowood-original-bfbab207.tar.gz`，384 members／317,049 bytes，SHA256 `bcb8dfacbc3c20f7e7b25b279502c03b0d9d1e7fb2f496dc948927b985522819`；逐檔 bytes/hash 在 `MEMBER_HASHES.json`，環境、完整指令、退出碼與 SHA 均保存 |
| 全專案列車與帳本 | 本分支尚未採入列車 closure，本 13／七階段綠不能外推列車全綠；整合後由 root 判斷帳本及重跑範圍。本分支未自行重產帳本 |
| 允許 skip | 無 |

本輪保留原 driver／test／capture 位元組、全部時限與 EX|NB。root 為第 2 個 C 時槽明確配置 `/tmp/g261r3/secondary.lock`；只調整既有 `--heavy-lock` 參數，原第 1 槽帳本鎖不動。原 `REQUEST.json`、新 `REQUEST_SLOT2.json`、差分與授權記錄均封存，忙鎖仍走原 exit 2，不重試繞過。

原件包含 77 份各階段來源、精確變異／還原、全部 c387 Python pipe 位元組，以及 65 筆編譯／連結的原 argv、exit、完整文字 stdout/stderr，原 native 記錄共 121 筆。原編譯器採 text capture，未另存 raw compiler pipes；暫存 C／ELF 依既有 cleanup 清除。這些限制未以事後重建補作原件；literal include 檢查也不冒稱完整 C preprocessor closure。

未 merge PR、未 rebase、未 force push。合入及全專案最終驗收由列車後續處理。
