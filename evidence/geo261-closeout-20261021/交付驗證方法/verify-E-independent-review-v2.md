# E 驗證器修正版獨立只讀複核

已完整讀取修正版 `verify_E.py` 340 行、`guard_controls.py` 144 行及 `guard-controls-v2.json` 的 57 項控制結果。原件 SHA-256 已實讀核對：

- 驗證器：`ffe3d3fe08ba3c51534b51724ae984e9c3a3774b02230e6d0f344f1bc4d897e3`。
- 控制器：`49ca6d91aa286d62631063fc3a72aab0b9fd08d595ef5a9011090085aa4c43f2`。
- 控制原輸出：`a1b53ea229b3b4cf0a3ed9baa66de43e9f0483b9e04de4d5cb4b83e06be149d9`。

結論：首輪指出的兩項缺口均已在修正版處理，未見新的實質放寬或 repository 寫入路徑。可把本版作為待執行的交付驗證方法封裝；這不是 E 已驗證、E 可合併或產品驗收通過的結論。

## 首輪發現的修正

1. `verify_E.py:25–31、103–105、250–254` 補回 12 個副檔名，並對每份證據 bytes 拒絕 ELF、MZ、WebAssembly、Mach-O／Java 與編譯封存標頭。原 `.txt` 文字來源、PNG 與 gcanvas 的控制正例保留；不把文字 shebang 等同有執行權限。既有一般 blob／模式／父層 symlink／原 bytes 與 Git oid 檢查維持。
2. `:122–134、279–299` 先核固定 L 的 source bytes，再按 binaries、run_tests、mutation_bridge、mutate 的順序建立 ModuleType，直接 compile／exec 已核 bytes，且拒絕預載同名模組、失敗移除暫存模組。沒有將 tests 路徑加到 sys.path，也不透過來源載入器讀這四個模組的 pyc。依賴 AST 盤點限制已知非標準函式庫集合，避免偷偷改回未綁定模組。
3. `:199–212` 另加入證據實體檔案集合核對，涵蓋 ignored 額外檔案；walk 錯誤、symlink、非一般檔皆拒絕。它補足首輪只有 Git tree exact set 的範圍限制；最終 Git tree 與實體檔案都必須等於外部 review 集合。

原本的精確總 diff、每 commit 白名單、固定 L 快照、外部 review hash、index 自身 hash／精確自我排除、三行 gitignore 與一行 attributes 追加規則均維持。未把新根全部忽略種類泛開。

## 本代理的輕量獨立核對

只讀命令以 `git show 43f85313c32410ac01406ab585846bbacafea278:tests/<name>.py` 取得四份固定 L 原碼，再用 `ast.parse` 及 AST walk 盤點 import；未 import 或執行任何產品／正式裁判模組。工具結束碼 0。實際非標準函式庫依賴如下：

| 模組 | 依賴與固定 L 行號 |
|---|---|
| binaries | 無 |
| run_tests | 無 |
| mutation_bridge | mutate，:171（函式內） |
| mutate | binaries :78、run_tests :79；mutation_bridge :867、999、1094、1439（函式內） |

聯集恰為 binaries、mutate、mutation_bridge、run_tests，與修正版要求一致。載入順序亦符合頂層實際依賴，沒有為驗證而啟動 mutable main、測試或編譯。

57 項拒絕與前後合法資料通過是已保存控制原輸出與代理實跑回報；本代理只讀核對，未重跑。其範圍為純資料守門及記憶體小模組，不含真正 E 工作樹的 Git／filesystem／正式 hash 路徑；不能把這些控制稱為產品突變 killed 或 E 已通過。

## 仍須保留的界線

E 尚未存在，驗證器本體未執行。最終真正原件集合、權限、ignored 檔案、Git attributes、提交鏈與 L→E source bytes 必須等 E 形成後按實際收據判定；不能用只讀審查或控制輸出預填。型態辨識是明列副檔名與格式標頭的契約，不宣稱所有任意封裝格式都已分析。

首次來源／31 項控制／首次審查均保留；修正版的結果另存，不回寫首次為通過。本代理未修改 repo、原始收據、凍結包或驗證器，也未執行全包 hash、正式 `mutate.py --check`、產品測試、瀏覽器或建置。
