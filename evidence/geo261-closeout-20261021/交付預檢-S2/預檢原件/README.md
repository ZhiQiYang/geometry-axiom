# S2 後、L2 前的有限交付預檢

本輪只讀目前 `final-bundle`，不修改主 repo、凍結包或舊索引，不執行產品測試、建置、E verifier 或新負控制；沒有產生最終 `artifact-index.json`。L2 與其完整驗收尚未出齊，以下不是最終交付驗收。

2026-10-21 03:24:54.430607Z 至 03:24:57.749782Z 的一次掃描共 **19,540 檔、208,687,311 bytes**，耗時 3.319185 秒。原件在本目錄 `summary.json`、`file-observations.json`、`submanifest-checks.json`。前後檔案集合、size／mtime／mode 沒有變化。

由已審 `verify_E.py` 原碼（SHA-256 `ffe3d3fe08ba3c51534b51724ae984e9c3a3774b02230e6d0f344f1bc4d897e3`）只做 AST 讀取，沿用其禁用 suffix、ELF／MZ／wasm／Mach-O／archive 等 magic 規則。一般檔、symlink、執行位元、巢狀 Git 規則與檔頭核對皆無發現；合法 PNG／gcanvas 與含 shebang 的文字來源沒有被當成可執行檔。未執行 verifier 主程式。

檢查 24 份 `SHA256SUMS` 與 16 份明列 JSON 子索引，共 21,333 筆引用（有重疊，不能當獨立檔數）。所引用的內容 hash 與提供的 bytes 全相同，沒有 missing／mismatched／invalid 條目。歷史原始索引、外部二進位封存索引不是 curated 包的 exact set，沒有冒稱全部索引都可依原路徑在包內解析。

`python3 -B /workspace/geo261-evidence/bundle-preflight-S2.py` 的實際結束碼為 **1**（工具紀錄 `b1c799`），唯一觸發是接受器把 `後續工作/issue300-readonly/原件索引.json` 當成包全集合，將未列其中的 `README.md` 報為 extra。完整閱讀後確認索引只列五份外部原件，沒有聲稱包含本地新增 README 或全包 exact set；五份原件的 hash 全正確。這是接受器範圍推定過度，不是凍結包 hash 破壞。原 `summary.json`／`result.json`／`command-code.txt` 與真碼保持不變；沒有重跑整包掃描或回寫索引。README 仍須由最後總索引覆蓋。

ignore 只在本目錄的空暫存 Git repo `ignore-model/` 模擬，不碰主 repo。保存原 `.gitignore` 與精確追加三行的版本，對全部預定證據路徑執行真 `git check-ignore --no-index -z --stdin`：

| 規則 | 真結束碼 | 被忽略路徑 |
|---|---:|---:|
| 現有 repo 規則 | 0 | 19,540 |
| 加入原定證據根、build.log、server.log 三行 | 1 | 0 |

後者 exit 1／空 stdout 是 Git 的「沒有路徑被忽略」，不是失敗。三行以外沒有擴張白名單。`.gitattributes` 的精確新增 `-text -whitespace` 版本也保存為文字，但沒有套用至主 repo。此模型關閉使用者級 excludesFile，不能替代最終 E2 真 checkout 的 ignore／attributes 驗證。

既有代理只讀原件引用與小 JSON 後，我再用本輪檔案 hash 清單反查完整內容，確認以下 **5 份 JSON 原 bytes 尚未收錄**，可由 root 後續追加外層附錄，無需改任何凍結子包：

| 包外原件（均在 `/workspace/geo261-evidence/`） | 同 stem 退出碼原件 |
|---|---|
| `ledger-cc-7159530c0e49.wzi0t97l-publication-check.json` | `ledger-cc-7159530c0e49.wzi0t97l-publication-check.exit-code`，0 |
| `p189-final-L-package.receipt.json` | `p189-final-L-package.exit-code`，0 |
| `p189-codec-candidate-package.receipt.json` | `p189-codec-candidate-package.exit-code`，0 |
| `p189-contact-v2-package.receipt.json` | `p189-contact-v2-package.exit-code`，0 |
| `architecture-owned-S2-package-receipt.json` | 沒有同 stem 獨立碼檔；收據本身由已記錄真 0 的包裝命令產生，不補造 |

歷史 GCC ledger 的 publication-check 已以相同 bytes 收在 `ledger-A-gcc/integration/publication-check.json`，同目錄亦有具名退出碼／stdout／stderr，**不列缺件**。僅依原檔名查找的首次外層接受器誤假定六份都缺而 exit 1（工具 `f8af33`）；原碼、結果、退出觀察分別保留於 `outer-receipts-code-attempt1.txt`、`outer-receipt-observations.json`、`outer-receipts-attempt1-observation.json`。改為依實際 hash 分類後，同一小型原件查核 `python3 -B /workspace/geo261-evidence/bundle-preflight-outer-receipts.py` 真 **0**（工具 `971a8e`），結果在 `outer-receipt-observations-v2.json`／`interpretation.json`。這次只重讀六份小 JSON，沒有再掃整包。

現有 P-189 父程序 wait 原件、footprint 兩份 packaging、host-copy packaging 與 contact diagnostics curate 皆已有包內對應，不列缺件。外層收據查核不聲稱涵蓋所有未來交付文件。最大的未定項是新 L2 帳本、來源 snapshot、同源完整驗收與最終草稿尚未齊；本預檢不能代替最後的精確總索引與 E2 驗證。
