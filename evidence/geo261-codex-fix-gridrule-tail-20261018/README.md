【Codex】gridrule 額外尾欄修正已完成修前、修後及 W／H 各自撤回的真實證據，恢復後完整相關兩套 **50/50 通過**。產品修正為 `c2bad7f3bd9024583b5314f968dafaba1abb626f`，分支 `codex/geo261-fix-gridrule-tail-20261018`，基底 `1987af507c6f387d7986325da6c29b2ec6246944`。本檔為待發布報告，不代表已留言或合併。

分類：**產品缺陷，根因已存在 main**。正式引用語法依基底 SSOT 的 R32 第 2243 行為 `gridrule:G:S:K:I:J:u|v:INDEX`，前綴加七個身分欄位，恰八欄。H 與 W 的 tokenizer 原本在第八欄仍把下一個 colon 改成 NUL，後續既有拒絕額外 colon 的條件因此看不到第九欄。修正只在兩處增加 `n==8` 停止條件，保留原欄位、數值、非零 key、軸、signed cell 與長度檢查。

main 的 H tokenizer 可追溯至 `68ac8a21c569aaf60f79e1d31128044be85db4d9`；integration `39f5ee8c` 搬移規則策略時保留缺陷，新增 W 驗收揭露它。這是歷史來源證據，沒有宣稱本輪也在 main 動態重現。R32 的失敗原子性仍由既有公開 bridge oracle 驗證：非法載入必須拒絕，保留完整 snapshot、pending confirm 與 undo。

| 階段／被測 SHA | 原始結果 | unittest 秒 | 原件 |
| --- | --- | ---: | --- |
| tests-only `24e780f9` | 10 方法，8 過、2 失敗方法，共 3 次 failure 事件 | 37.695 | [stderr](before/command.stderr) |
| 修後 `c2bad7f3` | 相同 10 方法全部通過 | 39.741 | [stderr](after-focused/command.stderr) |
| 只撤 W `a3bad6f0`（本地負控） | 1 方法、1 failure | 7.497 | [stderr](withdraw-w-only/command.stderr)、[patch](withdraw-w.patch) |
| 只撤 H `bcd3e24a`（本地負控） | 1 方法、2 個 subtest failure | 37.973 | [stderr](withdraw-h-only/command.stderr)、[patch](withdraw-h.patch) |
| 恢復 `c2bad7f3`，完整相關兩套 | W 9/9、H 41/41，共 50/50，無 skip | W 4.561／H 120.843 | [stdout](restored-full/command.stdout) |

W 修前與撤回的具名原文均為 `AssertionError: 0 != 1 : references: ASSERT:references:63`，對應原有非空 `:extra` 尾欄拒絕。該輪先在原斷言停止，新加的空尾欄檢查尚未抵達，不能宣稱 W 的兩種尾欄都分別轉紅。H 修前與獨立撤回均在 `extra-reference-field`、`empty-extra-reference-field` 兩個 fixture 出現 `AssertionError: True is not false`；原始成功回覆與 revision 留在 log，沒有改寫成泛化錯誤。

兩個負控只撤回各自一個產品檔的停止條件，保留另一層修正及全部測試 bytes。[W commit 原件](withdraw-w-commit.txt)、[H commit 原件](withdraw-h-commit.txt) 與 patch 均逐 byte 對照 Git 物件；本地負控 SHA 不冒充已發布分支。原 C harness 的 CHECK 全保留，追加空尾欄 CHECK_NAMED；原 Python 41 方法、321 個 assertion AST 全保留，只把既有 atomic-load 方法 fixture 從三個增加到五個。沒有刪除或放寬斷言，沒有更改 SSOT。

定向命令為 `python3 -B -m unittest -v tests.test_geo261_native_grid_rules tests.test_grid_subdivision_oracle.NativeSubdivisionOracle.test_saved_rule_reference_missing_key_wrong_source_and_index_reject_atomic_load`；撤回各自只選同一具名方法。恢復完整相關回歸命令為 `python3 -B -u tests/run_all.py --build --only py:test_geo261_native_grid_rules --only py:test_grid_subdivision_oracle`。最終 suite JSON 為 W 4.68／H 120.98 秒，runner 顯示 4.8／121.1 秒；含建置外層 156.991594092 秒、exit 0。五輪均無 timeout／interrupt，receipt 記錄 source／HEAD／status-diff 穩定，最後兩套 logs 完整封存。各輪完整 argv、來源 SHA、UTC 起迄、exit、外層耗時、原失敗訊息與原件 hash 見 [results.json](results.json)。unittest、suite JSON、runner 顯示及含建置外層耗時分列，不互相替代。

環境：Debian 13.6／Linux 6.18.55 x86_64、GCC 14.2.0、Python 3.12.14、Node 24.19.0、Google Chrome 155.0.8059.84、Chromium 154.0.8037.57；子程序 stack 16 MiB。本階段沒有跑瀏覽器。

公開範圍為原 command stdout／stderr／process、receipt、suite logs、binary sidecars、版本輸出及兩個負控 patch／commit。原 recorder 與每輪兩份大型 source.json 不複製；[inventory.json](inventory.json) 保留收據記錄的 SHA／大小與此限制，不聲稱公開資料足以重算未公開的逐檔來源清單。沒有複製產品 executable、Python 工具或整份工作區。原始 receipt 內列出的其他擷取檔不一定在公開 payload，公開集合以 inventory 為準。

未驗：main 動態重現、修正合流後全量非瀏覽器／六 browser jobs／完整 mutation registry、Windows/MSVC/GDI 與其他整合驗收。兩套相關回歸通過也不能代表全部驗收完成。
