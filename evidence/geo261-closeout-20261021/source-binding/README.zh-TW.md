# A → L → E 來源綁定唯讀審查

目前產品來源 A 為 `7159530c0e494d3211e6ab1764eb691137211707`，分支 `codex/geo261-closeout-20261021`。第一次帳本提交 L1=`cd4ac98f44174729fb3a2f1c291c6c258c9a239a` 的預設 CC 正式 check 回 1，因此未採用、未推送；最終 L 尚未提供，E 尚未建立。詳見 L1-README.zh-TW.md。本文件是來源策略與保存清單；不宣稱來源阻擋或合併阻擋已解除，也不預填 L 的結果。

審查依據為 `../final-bundle/review/最新審查原文.md`。第 3 行的「7dae 最後 push 後唯一留言」是使用者確認；第 11–12 行的審查對象是 7dae；第 35–39 行是本輪回應方案，不是審查者核准。第 7 行的本機 merge commit 說明也不是審查留言。新候選仍須依第 31 行「修正以上 3 項後再審」。本環境沒有透過 GitHub API 取得或更新留言。

## 結論與可接受的表述

A 完整重產帳本、L 僅提交帳本且實際執行全部最終整合清單、E 僅交付文件證據與精確 Git 設定附加，能形成可稽核且不循環的回應方案。前提是下列綁定全部據實保存；來源可稽核不等於行為驗收通過，P-189 等紅燈也不能藉來源同一性改成綠燈。

正文應分列「產品與架構來源 A」「帳本及最終整合 checkout L」「證據交付 E」。另明寫：75 筆帳本 execution 實際受測 A；最終整合清單實際受測 L。不能簡寫成「所有測試都在 L」，不能改寫 execution.head，不能稱帳本在 L 重產，也不能稱整合已在 E 重跑。7dae、R2、A 預檢保留歷史標示，current 矩陣只列 L 真實結果。

## 正式工具實際檢查的範圍

| 項目 | 正式實作 | 能證明及不能外推的範圍 |
| --- | --- | --- |
| execution.head | `tests/mutate.py:1012`；`tests/mutation_bridge.py:379` | 只驗 40 位小寫十六進位格式；不驗該 commit 可解析、不驗它等於 checkout HEAD，也不查遠端。須另做 Git／實跑來源綁定。 |
| include closure | `tests/mutate.py:642–672` | 從 `current_geometry.c` 與存在的 `geometry-web/web_bridge.c` 出發，遞迴讀取能解析、仍在 repo 內的 quoted include 聯集；CRLF→LF 後逐檔雜湊，再以排序路徑／hash 組合。不是一般 C preprocessor 的全部環境證明，也不包含 app.js。 |
| core oracle | `tests/mutate.py:675–690` | `tests/run_tests.py` 加 TESTS 引用的去重、排序場景檔，全部 CRLF→LF；缺檔以 MISSING 記號入 hash。 |
| bridge oracle | `tests/mutation_bridge.py:74–83` | 指定 methods、RESTORED 方法清單、flat `tests/*.py`、repo 根目錄 `*.scene`；不是遞迴所有 Python。明文排除帳本，避免自我雜湊。 |
| mutation tool | `tests/mutate.py:1057–1062` | LF 正規化的 mutate.py，加 `\0mutation_bridge.py\0` 分隔與 mutation_bridge.py 內容。不是完整 Python／GCC／系統環境指紋。 |
| mutant definition／record | `tests/mutate.py:840–845,967–975,1091–1133` | 檢查定義、來源、closure、oracle、tool、record checksum、執行結果一致性；record checksum 偵測意外修改，不能代替來源可取得證據。 |
| compile fingerprint | `tests/mutate.py:693–704,1014–1019` | POSIX 綁命令參數、Windows 綁 _cl.bat；不等於編譯器 executable／版本本身。環境需另保存。 |
| `--check` | `tests/mutate.py:1453–1473` | 只讀評估並回傳結束碼，沒有 save_records，不編譯、不重跑行為。blocked→2；survived/invalid/stale/unrun→1；其餘→0。 |
| 架構 inputs | `closeout-tools/refresh_receipt.py:20–26,51–67`；`tests/test_product_architecture.py:83–88` | 五個產品根中的可執行副檔名，另加 current_geometry.c、tests/__init__.py、tests/binaries.py。帳本 JSON 不在其中；四個 derived metadata 另綁 bytes，不自我納入 closure。 |

帳本 JSON 同時不是 mutation closure、兩種 oracle、tool hash 或架構 inputs。A→L 若精確只改帳本，這些來源值可以相同；這是內容同一性，不是帳本「在 L 執行」的證明。

## 必須保存的明確綁定

1. **可取得來源**：A、L、E 的完整 SHA、tree、父節點、分支／ref；實際 push 命令、exit、raw，及可解析遠端 ref 的唯讀核對。A 必須可從推送的 L／E 祖先找到。`git cat-file` 僅證本地可解析，不能冒充 GitHub 已公開；目前「A 已 push」來自主代理完成紀錄，本次未另連遠端。
2. **A 的完整重產**：不帶 mutant ID 的正式 CLI argv、cwd、開始／結束 UTC、實際 parent returncode、完整頂層 stdout/stderr、環境／工具版本、唯一 cache/results 路徑與執行前後 HEAD／source hashes。保存 A 原帳本與新結果原 bytes，78 定義 ID 集合、75 非 retired 的 execution.head 全為 A；3 retired 不偽造 execution。逐筆保存 source/closure/oracle/tool/mutant/record hash、baseline、attempts 與分類；不預設舊 70/1/4/3 結果必重現。
3. **新帳本的 check**：保存實際 `python3 -B tests/mutate.py --check` 的 checkout SHA、MUTATE_RESULTS／MUTATE_CACHE／CC、argv、完整 raw、真 exit，以及帳本執行前後 raw hash。原文第 17 行要求 check=0，沒有明文要求 A、L 各跑一次；若兩次實際都有就分列，缺一次不能補稱。L native 的 mutation:check 如被用作 L check，須具名保存該 suite log／exit，不能只借 native 總結。
4. **A → L**：保存完整父子鏈及每段差異；A 必須是 L 的祖先，A 之後到 L 的每個提交只能修改帳本。已知 L1 的 parent 為 A；後續新 L 依主代理方案以 L1 為 parent，保留失敗歷史。`git diff --name-status A L` 總差異仍只能有 `tests/mutants_results.json`；`git diff --exit-code A L -- . ':!tests/mutants_results.json'` 為 0。L ledger blob 原 bytes／SHA-256 必須等原 A、預設 cc 完整重產輸出，不能只比較解析後 JSON。對新 ledger 的每筆 execution.head 明確比 A，另保存 closure/oracle/tool 與 compile command/hash 定義及實值；不得改標 L。
5. **產品與架構**：對 A/L 的 app.js 等全部架構 inputs 611 路徑和 raw／LF hashes、四份 metadata、三份架構裁判做明確比較。收據 sourceBaseHead 仍是 S=`ab6869b86a4ad82345359b72397fc055280d8308`，S→A 綁定由既有 metadata-binding-v3.json 提供；不能為 L 把舊收據內的執行 SHA 回填。與 7dae 比較時仍須承認 owned app.js 已改，不能再說 333 owned 全部 bytes 相同。
6. **L 實跑清單**：native（實際 `tests/run_all.py --build`）＋ canvas、assembly、documents、grid、space、timber 六 browser，共七項；再加 Q38、兩個 §7 入口、原 12 裁判控制、P-189。replay 若包含在 native，具名保存 `py:test_geo261_model_base_replay` 的同 L log／JSON，不要求重複執行也不借歷史結果。每項保存 checkout L、起訖 HEAD／source hashes、argv/cwd/env、fresh binary／runtime、完整輸出、外層與內層 exit、timeout／signal、skip 原因與結果範圍；未完成或紅燈照實列出。
7. **L → E 精確白名單**：保存全差異列表及每檔原 bytes hash，E 只可新增核准的文件證據及下列 Git 設定附加；產品、測試、場景、ledger、架構 inputs／裁判／四產物維持 L bytes。比對應涵蓋新增檔案集合，不能只比較既有 receipt 中列出的路徑。新執行來源若進五個產品根，即非單純證據交付，不能沿用本策略。
8. **E 的 Git 設定**：`.gitattributes` 保留 L 的全部原 bytes，只附加新證據根 `evidence/geo261-closeout-20261021/** -text -whitespace` 的精確規則；`-text` 保留跨平台 checkout bytes，`-whitespace` 避免把 raw log 的原始尾端空白當產品程式碼問題，其他產品路徑的檢查維持。`.gitignore` 只追加新證據根與該根內 build.log/server.log 的精確白名單，最終逐行核對，不允許泛化忽略產品路徑。不得為通過 diff --check 修改 raw 證據。提交後另驗有效 attributes 與 Git blob hash。
9. **交付索引**：外部原件 → E repo 相對路徑 → raw bytes／SHA-256 的清單，包含輸出／收據／實跑工具 hash／獨立審閱；歷史與 current 分開。索引若不雜湊自身，明列排除及原因。E 的完整 SHA 可由提交後 Git 查詢與最終回報給出，不在 E 本身假造能預知自身 SHA 的自封收據。
10. **PR #288 回應**：請使用者在 PR #288 更新正文為 A／L／E 分欄與 L current 矩陣、貼回來源阻擋對應與 repo 內可取得證據、請 ChatGPT 對新候選複審。尚有未完成／失敗項目時不可要求按「全綠已解除」合併；HANDOFF §7 的使用者待決事項仍不代決。

## 本次輕量驗證

已以外部 `snapshot_bindings.py` 使用正式 mutate／mutation_bridge 的只讀 hash 函式，於 A 執行：

```sh
python3 -B /workspace/geo261-evidence/source-binding-preparation/snapshot_bindings.py --root /workspace/geometry-axiom --expected-head 7159530c0e494d3211e6ab1764eb691137211707
```

結束碼 0；stdout 原件為 `snapshot-A.json`。起訖 HEAD 均 A，tracked clean。選定聯集 1,010 檔的工作 raw bytes 與 A Git blob 一致；這不是全 repository／全 runtime／binary 掃描。腳本讀既有 architecture receipt 的 counts，**沒有重新執行架構 gate**；它驗既有 611 inputs 及 closure，不額外證明未列入來源沒有新增。最終全差異及完整集合核對仍由第 4、7 項補足。

- mutation include closure：184 檔，`872824fc382cb0467591d8df22e375c2e9a6649578b170365246ada795fcce63`。
- core oracle：165 個場景，`f8222a4ac7ae76339cfb7536634f98e572ecd2bb0d649ce3395d6d452e2fa306`。
- bridge oracle 輸入：225 個 flat Python、171 個根目錄場景，加各自 methods／RESTORED；逐 mutant oracle hash 在快照內。
- mutation tool：`24c391b89880b8abc36cf4b7431afd1bb5486982cb9d41a6a0d975ac7c3c6387`。
- 78 定義＝60 core＋18 bridge，預期 75 execution；這是定義盤點，不是新帳本通過結果。
- 架構現有收據：611 inputs＝333 owned＋278 exclusions、796 edges、0 diagnostics；input closure `4be326e07260a35b456ef4e8d46f50c28432216f66e45c5afc56d46d5313ce9b`。

同一外部腳本將 expected-head 改成 7dae 完整 SHA，實際於 A 執行，結束碼 1，先於載入裁判拒絕；stdout 空、stderr 原件在 wrong-head.stdout／wrong-head.stderr。這只是來源守門負控制，沒有新增產品突變自證。腳本 SHA-256：`0640270f504fc0f12398cf15dda289f45dda188b9fa42cf3e32b862ee76a9a48`。

獨立代理 p52_review 已唯讀覆核審查原文、腳本與所呼叫函式，未發現本輪 A／新 Python 程序用法有副作用或阻擋；沒有重跑腳本，也沒有代替 L/E 驗證。腳本僅應以獨立 Python 程序使用，不嵌入已載入其他同名模組的程序。

未驗項：本輪沒有跑 mutation、--check、編譯、瀏覽器、效能或架構 gate；沒有驗未建立的 L/E，也沒有另向遠端讀 ref。core 正式工具目前只在帳本保存每次 oracle 的完整結構化結果與 stdout/stderr hash，未存每次子程序原 raw；不能把頂層 log 冒稱包含那些 raw，詳見既有 ledger-plan.md。最不確定的是審查者是否接受揭露完整的 A execution＋L 同產品 bytes＋L 整合實跑分層；不能替審查者宣布已豁免其來源要求，仍須再審。
