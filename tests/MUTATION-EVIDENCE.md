# 突變收據與可下載二進位證據

> **現行表（2026-11-12 依 `f3ee80cf` 實數更正）：138 筆／135 active／3 retired**；core 70（67 active＋3 retired）、bridge 68，七片依現行表動態分成 core 18／18／17／17 與 bridge 23／23／22（`.github/scripts/mutation_evidence.py::shards()`）。已採入的 `tests/mutants_results.json` 為 138 筆：killed 129、equivalent 5、crashed 1、retired 3（main 上最近一次採入為 `eca59df8`，Mutation evidence 43361431042）。
>
> 歷史：main `8f82b207e87c086705a1d8b7a00e2f215c07cbcf` 納入 #338 時完整表為 123 筆／120 active／3 retired（core 70、bridge 53，分片 18／18／17／17 與 18／18／17）。`de9aea24113a522c6cd80d30b9281e1034b57c6c` 的 [run 41333327153](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41333327153) 及 78／75 收據保持原來源的歷史證據。

`tests/mutate.py --check` 不編譯、不執行突變。它嚴格核對來源、include 閉包、突變、裁判及執行收據。若同平台的暫存二進位存在，也會核對它的指紋與 SHA-256；不同二進位應判 `stale`。沒有暫存檔時通過，只能證明收據與目前來源／裁判一致，不能宣稱已核對原執行檔位元組或已重跑突變。

因此 #357 `212ee528` 的 [run 40939418733](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/40939418733) 中 `mutation:check` exit 0，與另一工作區出現 75 筆暫存二進位不符可以同時成立。前者是乾淨環境的收據驗證；後者仍須保留拒絕結果，不能只稱為環境差後忽略。

## CI 的新證據

`Mutation evidence` 工作流程不改 `mutate.py`、`mutation_bridge.py` 或已提交歷史帳本：

1. 先在 GitHub 執行原 scanner CLI 與原兩支架構 unittest，保存新來源的 scan／receipt／說明與原始輸出；沒有在本機執行模組。歷史帳本的原 `--check` 守門仍保留在正式測試入口；來源改變時，歷史 stale 不能拿來阻止「生成新收據」，也不能被寫成已通過。
2. 從現行突變表自動分成 4 片 core 與 3 片 bridge，每筆恰好一片。新來源的全部 active（現行 135 筆）均需實際執行（含 equivalent 的完整 oracle），3 筆 retired 仍核對退役條件。bridge 還原裁判為 `tests/mutation_bridge.py::RESTORED` 的方法（現行 55 個），裁判閉包也包含 `tests/*.c` 與 `tests/fixtures/**/*.scene`，不能把舊 75 筆冒成 fresh。各片結果檔從空檔開始，不繼承歷史 killed。
3. 各片使用原 runner 執行基準與突變，保存新帳本、實際二進位／sidecar、執行輸出及雜湊 manifest。core 保存結構化 oracle 執行收據與 runner 輸出；bridge 另保存逐次建置及 oracle 的原始 stdout／stderr。省略 scratch checkout 與 OS core dump。
4. 每片要求全部指派 ID 存在、實際收據屬於當前 head，並用原工具 strict 檢查。刻意改壞一個該片二進位，必須被原二進位守門拒絕、strict exit 1；還原 bytes 後重驗通過。`blocked`、`stale`、未知／缺漏 ID、skip 或基礎設施失敗都不算 killed。
5. 聚合 job 必須等所有片成功；重新下載 artifact，逐筆要求二進位存在且 SHA-256 相符，再以原工具核對每片。最後要求完整表無重複／缺漏／額外 ID，對新完整帳本再跑原 strict 檢查。

`mutation-shard-*` 是原執行證據；`mutation-complete-evidence` 包含聚合帳本及 `summary.json`；`pr357-architecture-refresh` 保存原三命令的新架構衍生資料與 raw 輸出。完整 Mutation evidence 仍從空帳本真跑每片，不把下面的儲存格式改動當成增量執行或免驗二進位。

## Repo 內的不可變證據與當前視圖（issue #214）

基準為 `11eddfdb4d7b1f76aedfe001e084a3840790bedc`。採用方案 (c)：降低衍生檔的共同改寫，並把架構重驗從全量突變中分出獨立入口；沒有縮小來源／裁判／工具閉包。基準實數仍為 138 筆（core 70、bridge 68）、55 個 bridge RESTORED 方法；survived／invalid／blocked／stale／unrun 均為 0。

### 突變

`tests/mutants_results.json` 在 Git 中保留固定 seed，`seed.json` 釘其 blob、bytes 與 SHA-256。工具以 `git show HEAD:tests/mutants_results.json` 取 seed，不信已物化的工作樹視圖，也不要求未來的 shallow checkout 保有舊基準 commit。不能再提交覆寫這個歷史路徑。

新紀錄放在 `.github/evidence/mutations/objects/`；每個 ID 的明確引用放在 `refs/`，沒有更新的 ID 沿用 seed。缺物件、錯 ID、壞 hash、重複 JSON key 或引用損壞都拒絕，不退回另一份綠燈。每筆的所有原 record 欄位、`record_sha256`、`execution.head`、命令與結果保留；分檔會重新序列化 JSON 外層，不宣稱與原帳本 byte slice 相同。原 `summary.json` bytes 另存於 `origins/`；其完整原 ledger 以可逆 gzip 封裝放在 `ledgers/`，解壓 bytes 必須符合原 summary 的 ledger SHA，每筆 selected record 也必須與該原 ledger 的同 ID 完全相等，避免把同 head 另一個 run 的紀錄錯掛來源。這會增加 repo 原件儲存，但不產生共用可變路徑；沒有只存外部連結。

採入前先對完整新 artifact 驗 schema、來源、ID 全集、ledger hash、原 strict 收據與結果。即使原引用仍 fresh，新帳本有 survived／invalid／blocked 也不能被忽略。完整新帳本合格後，原引用仍 fresh 的 ID 不改寫；只有 stale／unrun 才換新實跑收據，避免每次全量產生物把整表都改一遍。

```sh
# 下載正式 Mutation evidence 已通過 verify 的原完整產物。
gh run download <mutation-run-id> --repo ZhiQiYang/geometry-axiom --name mutation-complete-evidence --dir <完整產物目錄>
python -B .github/scripts/evidence_records.py adopt --root . --artifact <完整產物目錄>
python -B .github/scripts/evidence_records.py check --root .

# 物化後才執行原入口；物化的舊帳本路徑不提交。
python -B .github/scripts/evidence_records.py materialize --root .
python -B tests/mutate.py --check
```

提交 `.github/evidence/mutations/` 的新增原件、來源與必要引用即可。`Geometry integration` 在各 native checkout 先物化，原 `run_all.py` 仍把 mutation-check 固定指向 `tests/mutants_results.json`，原 120 秒不變。`repo evidence freshness` 另核完整 store；它不接受缺少某 ID 或未知多出 ID。沒有物化而直接跑原 `--check` 時，讀到的是 seed；來源變動後它會保守報 stale，不能把這個失敗當成已驗過新引用。

這裡的 check／materialize 只證明目前來源與原執行收據相符；不編譯、不跑突變，也不重新核對不存在的二進位。新物化的混合歷史視圖不沿用 `binary_bytes_verified: true` 宣稱本次 bytes 已驗。若要重驗原二進位，仍用下一節的完整 shard artifacts 與原 supervisor。

### 架構

原 `PRODUCT-ARCHITECTURE.md`、`product-architecture-receipt.json`、`product-architecture-scan.json` 在 Git 保留固定歷史 bytes。新三份衍生檔與六份原始 stdout／stderr，原樣放在 `.github/evidence/architecture/<完整輸入鍵>/<receipt SHA-256>/`。沒有全域 `latest` 指標，不覆寫舊報告。

目前輸入鍵包含完整來源與 exclusion 閉包、manifest、scanner、兩支測試與 generator。選擇前重新查完整 inventory，新增未登錄來源也會被拒絕；不能只檢查舊收據自列的 640 個路徑。三項原命令、完整非零 unittest 計數、零 skip、scan 零 diagnostics、所有 raw hash 都須相符。原 sourceHead／runId 保留，merge SHA 不同但完整輸入相同可以沿用；不同就需要原三命令的新實跑，不能拼接局部綠燈。

完成下面首次遷移後，只有架構證據過期時，從 PR 分支執行獨立的 **Architecture evidence**：

```sh
gh workflow run architecture-evidence.yml --repo ZhiQiYang/geometry-axiom --ref <PR分支>
gh run download <architecture-run-id> --repo ZhiQiYang/geometry-axiom --name architecture-repo-evidence --dir <bundle下載目錄>
```

將下載目錄中的完整輸入鍵目錄原樣加入 `.github/evidence/architecture/`，然後：

```sh
python -B .github/scripts/evidence_architecture.py check --root .
```

bundle 的封裝在原執行 head 的乾淨 CI checkout 完成；下載後只原樣採入，不在較新的採入 head 重寫原件的 sourceHead／generator hash。需要閱讀報告時可加 `--materialize <repo外的新目錄>` 產生視圖，不回寫歷史三檔。完整 Mutation evidence 也產出同名 `architecture-repo-evidence` bundle，所以真需全量突變時不用多跑一次架構工作。

獨立架構工作只執行原三命令，成功不代表跑了突變；沒有 mutation summary，也不會解除 mutation freshness、Geometry native／browser 或當下 head/main 終審。

### 遷移與合流界線

1. 套用工具與 CI 連接後，首次由 repo 已存在的 **Mutation evidence PR 執行**產生並採入 `architecture-repo-evidence`，不依賴尚未落到 main 的新 dispatch workflow。舊歷史三檔缺少 raw bytes，不能填 hash 冒成新 bundle。**本補丁本身不包含尚未執行的正式 CI 收據**；尚未採入時新架構 gate 必須紅。合併後的架構單獨更新才用新的 Architecture evidence。
2. 基準 seed 的 138 筆先由原 strict 判定，不改內容、record hash 或 execution head。來源確實過期才觸發原完整 Mutation evidence，再採入原件。這個版本沒有新的 incremental shard runner。
3. 合併前在實際合併結果跑 Geometry 的原守門。內容雜湊檔可合併並存；不同 ID 的引用分開。兩分支若更新同一 ID，引用仍可能衝突，不能任選 ours／theirs；在合流後核對來源，沒有適用收據就真重跑。
4. 舊 PR 若仍改那四個歷史路徑，先把有效原件依工具採入新 store，再把歷史路徑還原為固定 seed／baseline；不可丟掉新執行證據後只取 main 的綠燈。
5. 這個 store 版本支持新增 ID，以及原 ID 保留定義後 retired；刪除或改名既有 ID 會被完整集合守門拒絕，須另做明確的版本遷移，不得重釘 seed 解套。

此方案沒有解決 broad oracle 的所有假相依：修改 `tests/*.py`、`tests/*.c` 或受涵蓋 scene，仍可能使全部 68 筆 bridge stale。真正逐筆閉包至少要涵蓋每筆 `m.tests` 加上實跑的 55 個 `RESTORED`、傳遞 imports、fixtures、子程序與 build inputs，還須處理 dynamic import／glob／不存在路徑；不能只取該筆列出的測試名稱或一輪 open trace。這是方案 (a) 的另一項工程，不在本次補丁以刪斷言或縮 hash 代替。

證據繼續留在 repo，沒有 main 合併後再補證據的 stale 窗口；原正式 GitHub CI、原 timeout、原 assertions 與原 binary artifact verify 都不變。這個格式不免除現行 main 前進後的終審，也不承諾免除每次來源變更的整輪 Geometry。

## 從另一個乾淨環境重驗

需要 Git、GitHub CLI 與 Python 3.12 以上。使用該次 run 的完整 head SHA 簽出 repo，保持來源不改；下載 artifact 後，以下驗證只讀取二進位 bytes，不執行它們，也不重編：

```sh
gh run download <run-id> --repo ZhiQiYang/geometry-axiom --pattern 'mutation-shard-*' --dir <下載目錄>
python .github/scripts/mutation_evidence.py verify --artifacts <下載目錄> --out <新的驗證輸出目錄>
```

同平台保留原編譯指令／指紋的嚴格檢查；跨平台核對已下載的原執行檔 bytes 及原平台收據，不宣稱在接收平台執行了不相容的二進位。需要證明接收平台的行為時，須在該平台另跑原 runner，產生另一份執行收據。

artifact 保留 30 天。若要重新核對原執行檔而 artifact 已到期，須重新執行 `Mutation evidence`，不可宣稱舊 binary bytes 仍已驗；repo 中原收據則仍依原 `--check` 的完整來源／裁判／工具條件判定是否 fresh。來源、裁判或工具真的改變仍須真重跑。完整工作流程可手動啟動；更動此工作流程、監督腳本、儲存工具或本文的 PR 也會自動產生當前 head 的完整證據。
