# #314：提交只允許一軸相位差，保留舊雙軸場景

新建或增加第二軸相位差的提交現在依 I24 拒絕。舊雙軸場景仍可載入、重放、復原／重做；更名、間距與保值換來源可以編輯，仍為雙軸時直接改相位差值則拒絕並說明先在同筆編輯移除一軸。

依 2026-10-22 已鎖定決策，同候選先把相位參數 400 改為 500，再解除為直接 500 放行；解除為 450、反向先解除 500 再改參數均拒絕。W 擁有規則和訊息；H 在原操作時點以 fresh dependency closure 蒐集來源與有效值，把有序事實綁在同一候選、revision 與既有 operation seal，preview／confirm 使用同一份證據。確認仍完整重驗；事實不進 World、dump 或 history，取消、失效、失敗、成功及 dispose 都清除。

整批依最終軸數判斷，暫時雙軸而最終一軸的批次可提交；歷史群組依原規則逐行提交。既有通用 DSL `delete grid-system` 的真正刪除會終止例外，之後同 id 重建按新建；沒有新增 batch delete 指令。K、公理層與決策佇列未改，R60 的逐軸、零、節距整倍數、溢位與下游限制全部保留。

## SHA 與收據角色

| 角色 | SHA | 範圍 |
|---|---|---|
| 整合基線 | `4b665fae21ab63aaffb7d84f6a32d5a469ba1675` | 建在 #288 整合分支之上 |
| 集中產品／測試修正 P3 | `4f669733282613a6f1e4a627c448374716496daa` | candidate witness 初始化、ASM anchor、canonical 與 manifest 更新 |
| 舊帳本嘗試來源 S_old | `9b65f047d5fd470cdc89ce45e613d06af493b616` | 容量失敗及同來源 bridge 重試的真來源，原判決保留 |
| 原紅燈診斷公開提交 D | `01f1130fd0e93f61c698a963ee74ea349ac6820d` | 原容量失敗、環境重試及 M110 invalid 原輸出；保留原退出碼 |
| 最新 runner 修正 Pnew＝整份帳本實跑來源 S | `c4aad5d7bb98ea864639f9e6d85c99bb2613c24b` | 真 M110 修正撤回自證；原整份 `mutate.py` 在此乾淨 SHA 重產 |
| 帳本保存提交 L | `5c2c5dbd0bde8fe17097ae5243bfb27bbc2574f0` | 已一般推送；帳本 `execution.head` 保留真 S，不改標為 L |
| Linux 架構原三裁判／四檔重產來源 | `5c2c5dbd0bde8fe17097ae5243bfb27bbc2574f0` | 原三裁判退出 0／0／0；四檔 receipt 的 `sourceBaseHead` 保留真 L |
| 架構產物提交 A＝正式受驗 F | `cc67e2518f6ab331b5ab9fdbcd5bd6334134377f` | 已一般推送並核對遠端 SHA；七個原 job 的測試與 inner 均 0，原完整 ASM 與三架構亦通過；整輪出版退出碼另列 |
| F 的 ASM 收據保存快照 E | `8e15ddc6809ba68b706eaac2e9747cb2d6919007` | 一般推送保存同 F 專項原輸出；不是另一次產品受驗來源 |
| F 的三架構收據保存快照 E | `6ef61abd793a0aaa87de1b982fcd1d253cd7f018` | 三架構完成時的歷史公開快照；native 與 browser 收據由後續證據提交保存，這不是最終 E |
| assembly 出版修復公開快照 | `f5409cab927d45419b7afc7e86164a022ffd5399` | 原 publisher 只改 label 補發布退出 0；沒有重跑產品或改寫原 1 |
| 原完整終態封存提交 | `341532fa7e6453f70e2eaeb0e36a04d41afe419d` | 保原整輪 wrapper／outer 1、全部發布 streams、修復與摘要；原封包未改 |
| 完整驗收證據最終保存提交 E_final | `1e9f4873e6563bb4b90595bb1965532ea98619b3` | 已一般推送、遠端 SHA 相同且乾淨；F 後僅新增 `evidence/geo314-final-cc67e251/` 證據，E 不冒作產品受驗來源 |

## 已完成的修正自證

| 項目 | 真受驗來源與結果 | 自證範圍 |
|---|---|---|
| candidate witness 初始化 | P3 的 evidence descendant `c0a2007898f544e658efa72b9b51528a03f7ce51`；414 inputs 與 P3 相同；原 26 方法退出 0 | 只撤兩處新 `stagger_count/steps/seal` 初始化的合併變體，三原 case 各 0／1／0；具名正常 ASSERT 保存 |
| 原 canonical 同步 | 同 P3／`c0a20078`；原 51 方法前後均退出 0 | 舊 canonical 具名 idempotence 0／1／0；SSOT、白話、決策及 Backlog bytes 不變 |
| ASM cancellation anchor 重錨 | 新 S；本地已提交一行撤回 `238a5125c95e77d74603fdd943baaa81e140f7da` | 原 `test_mutation_anchors.py` 全三方法 0／1／0，負控兩條正常 AssertionError；這是 anchor 修正自證，不重標先前三個產品 mutants 的 killed |
| bridge equivalent runner 相容性 | 新 S；本地已提交撤回 `160e9dc9759aea2cd6b6f7c9eb717590924d1a24`；原 honesty 74 方法退出 0 | 原 M110 CLI／真 bridge 0／1／0；固定及恢復版各有 baseline／mutant／restored 0／0／0 的 equivalent execution 與原單筆 validator 通過。負控 invalid 且無 execution，不冒稱產品斷言 killed |

較早完整 native 診斷原退出 1，既有夾具缺檔、原 reader／帳本過期及集中修正前的失敗都保留原收據，不改標為本輪 F 的結果。第一輪整份帳本因容量問題原退出 2；同舊來源只重跑受影響 bridge 項時，M110 正確暴露 runner 尚不支援首個 bridge equivalent，原 invalid 保留。修正現在只允許「明示等價理由＋原 mutant 真 survived＋原 baseline/restored 全綠」映射為 equivalent；原 build、identity、oracle、死亡及完整性守門保留。修改 runner 後固定新 S，**不帶 IDs 的整份原 `python3 tests/mutate.py` 與原 strict `--check` 已完整退出 0**；97 筆 execution 全是新 S 的實跑，不沿用舊 execution 冒成新來源。

ASM anchor proof 的 001 已收錄原 baseline 0／撤回 1，但 collector 對 stderr 換行片語的預期失準，原 inner／outer 1 均保留。002 讀取同一份原負控 finding，只補缺少的 restored 0；沒有重抽前兩態、編譯或改原測試斷言。較早 ASM 完整工具／unit12／anchors3 原皆 0，但該次外錄製 guard 因 evidence 更新而退出 1，也依原值保留。

manifest 是明列 H 新來源、完整 W lexical guard union（920→928 identifiers；55 strings 不變）與精確 LF digest 的 metadata 更新。稀疏環境缺少的三個既有 ZIP 與一個 scene 以原 P2 Git blobs 精確補齊；兩受影響 Node 檔 94／94、graph 5／5 原退出 0，這些只屬 P2 環境重試，不取代正式 F 驗收。

## 整份帳本、架構與正式驗收

| 項目 | 結果與實跑 SHA |
|---|---|
| 新 S 原重產前 `mutate.py --check` | 原退出 1；完整輸出已隨 L 封存 |
| 新 S 原整份 `mutate.py`（不帶 IDs） | 原退出 0，2026-10-23 02:31:29 UTC 自然終態；100 筆：91 killed、5 equivalent、M20 crashed、3 retired；97 execution 全綁新 S |
| 新 S 原重產後 strict `mutate.py --check` | 原退出 0；inner／outer 亦原退出 0；新 S 前後 HEAD 相同且乾淨 |
| L 上 Linux manifest／scan／report／receipt 四檔與原三裁判 | 來源 L=`5c2c5dbd0bde8fe17097ae5243bfb27bbc2574f0`；原三裁判 0／0／0，driver 內外 0；產物已保存為 A＝F |
| F 原完整 ASM：`python3 -B /tmp/g261f314-cc67e251/tests/assembly_mutation_check.py --out /workspace/geo314-final-assembly-cc67e251` | 原工具與 outer 退出 0；summary `ok=true`，222.0 秒；baseline／restored 均 pass，三 mutants 具名正常斷言 killed，六 controls 全符合原判準 |
| F 原三架構裁判 | `architecture_contract.py`、`test_architecture_contract.py`、`test_product_architecture.py` 原退出 0／0／0；inner／outer 均 0，來源前後同 F 且乾淨，errors 空 |

原完整七項於 2026-10-23 03:28:54–04:42:46 UTC 依原 workflow 串行完成，全部受驗來源為 F。七個 job 的原測試／inner 均退出 0、`derived_pass=true`、`receipt_validated=true`、errors 空；各 job 前後均為乾淨 F，全部在各自原 CI 時限內。下表的發布退出碼獨立保存，不混算成產品測試碼。

| 原 job／收據 | 原測試／inner | 原秒數 | 原 CI 分鐘 | 原發布退出 | 原結果與範圍 |
|---|---:|---:|---:|---:|---|
| [native](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/receipts/native.json) | 0／0 | 1706.287484942004 | 35 | 0 | 227 suites；5,268＝5,267 pass＋1 允許的 Windows GDI skip，0 fail；`mutation:check` 0 |
| [canvas](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/receipts/canvas.json) | 0／0 | 1694.863327553001 | 35 | 0 | 2,267／0；原 full、golden matched；保 P38 預期例外 1 |
| [assembly](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/receipts/assembly-workflow.json) | 0／0 | 184.63856317900354 | 15 | 1 | 150／0；原 partial，`GEOMETRY_ASSEMBLY_ONLY`；出版修復另退出 0 |
| [documents](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/receipts/documents.json) | 0／0 | 61.946721535990946 | 10 | 0 | 47／0；原 footer 沒有 scope／completed 欄，不補造 full |
| [grid](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/receipts/grid.json) | 0／0 | 441.9847813739907 | 15 | 0 | 356／0；原 partial，`GEOMETRY_GRID_SYSTEM_ONLY` |
| [space](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/receipts/space.json) | 0／0 | 204.67509067499486 | 15 | 0 | 242／0；原 full-space-suite，保兩個 omitted timber groups |
| [timber](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/receipts/timber.json) | 0／0 | 121.76085274700017 | 20 | 0 | 79／0；原 partial，`GEOMETRY_TIMBER_ONLY`，保五個 omitted space groups |

原七項總 wrapper 與 outer **實際退出 1**，唯一原因是 assembly 原發布退出 1：原 publisher 的 `assembly-*.tar.gz` 守門撞到已存在的 `assembly-final` 專項封包。其餘六個原發布皆退出 0。整輪自然結束後，僅用原 publisher 將 label 改為 `assembly-workflow`，補發布原輸出，實際退出 0；原產品／測試沒有重跑，原收據與退出碼沒有改寫。這次 publication-only 修復 0 不取代原 wrapper／outer 1。[原終態與分層退出碼](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/ORIGINAL_RESULT_INDEX.json)、[出版修復原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/PUBLICATION_REPAIR.json)及原完整 streams 均已封存。

雲端原版本收據：`google-chrome --version` 為 `Google Chrome 156.0.8078.47`，`node --version` 為 `v24.19.0`，`fonts-noto-cjk` 為已安裝的 `1:20240730+repack1-1`；原命令皆退出 0。六 browser 的 `GEOMETRY_CHROME` 指向 `/workspace/geo261-environment/bin/google-chrome`，各用獨立服務埠 19081–19086 與 `/tmp/g261s7/tmp/workflow/<job>/`，環境、原指令、完整輸出及 SHA 都在各 job 收據與封包中。

原範圍如下，不把 assertion 數當成端到端情境數：canvas 原 coverage 明列 trusted input、DOM／programmatic integration 與 native API 混合；assembly、grid 原 partial 的 golden 不比較。documents 的原 coverage 是可信任指標／鍵盤導覽搭配合成檔案夾具及 PDF／safe Markdown 檢查，footer 未提供 scope／completed 欄。space 原 `full-space-suite` 明列 omitted `timber-material`、`timber-source-guards`；timber 原 partial 只含 `timber-material`、`timber-source-guards`、`font-layout`，明列 omitted `space-height-library`、`projection-lifecycle`、`projection-placement`、`space-flow`、`projection-close`。

canvas 原 stdout 第 1830 行「P73 空空間不畫假邊界，提供加入成員入口」與第 1855 行「P73 整輪沒有未處理瀏覽器例外」皆通過；1855 的文字僅指 P73 模組。整個 canvas footer 仍是 `uncaughtBrowserExceptions=1`：原第 561 行 `[EXPECTED EXCEPTION] Error: fb-auto-probe`，第 563／564 行確認 P38 自動擷取與預期單次例外抵達，沒有改稱整個 canvas 零例外。原 canvas 的 P53 transport failure、P57–61 network failure 與 assembly 的 `Injected lost success response` 也保留於原 footer，不改填空值。

P52-5 原第 773 行 `SYNC_WAIT` 為 240ms，原量測點是「角材 3 放置交易已收尾且核心 references 已回傳幾何」。它是正常 job 的同步等待紀錄，沒有擴成獨立首繪或 main／fix 三方 P-189 效能量測。完整原 footer、groups、scope 與行號見 [BROWSER_SCOPE_FACTS.json](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/BROWSER_SCOPE_FACTS.json)。

新增 M99–M120 的原判決是21 killed＋M110 equivalent；M110 的原 baseline／mutant／restored 均退出 0。M20 原連續同夾具存取違規照列 crashed，不改稱斷言 killed。安裝帳本後，原 canonical sync、reader `--check`、private-cache mutation `--check` 均退出 0；canonical bytes 沒有變更。

Linux 架構重產於 2026-10-23 02:33:33–02:33:52 UTC 完成：602 executable files、334 owned、268 exclusions、797 edges、0 diagnostics；H192／K69／W67／vendor6，W guard 928 identifiers／55 strings。manifest bytes 保持 L 原樣，沒有把 receipt 的真受驗來源改標為 A。146 個 raw 成員逐 bytes／SHA-256 解包驗同，archive 為5,872,249 bytes。這是 L 的四檔重產收據；之後在固定 F 另行執行原三條裁判，實際退出 0／0／0，兩輪的來源角色分別保留。

正式 F 的完整 ASM 於 2026-10-23 02:37:24 UTC 開始，原 summary 記錄 222.0 秒。`conflict`、`missing-source`、`cancelled-preview` 三個 mutant 都由 `exact-assertion` killed；六個控制均為 `not-killed` 且 `controlOk=true`，包含錯誤斷言、bridge crash、error、hang、single-layer 及 comment-only。各控制的非零／timeout 退出值按原收據保存，沒有把它們算成產品 mutant killed。`originalSourcesUnchanged=true`、`restoredBinaryMatchesBaseline=true`，problems 空。這次同 F 的真工具／outer 0 與前述 P3 診斷 outer 1、anchor proof 001 collector 1 是不同輪次，原失敗沒有改判。

正式 F 三架構的原指令如下，三者皆以 `python3 -B` 執行且退出 0：

- `tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`
- `tests/test_architecture_contract.py`
- `tests/test_product_architecture.py`

以下收據與索引全部連結至最終證據提交 E 的固定 GitHub URL；原真受驗來源仍分別保留 S、L 或 F：

- [整份帳本原命令收據與進度](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/tests/evidence/geo314-one-axis-stagger-20261022/ledger-c4aad5d7/PROGRESS.md)
- [逐項修正自證索引](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/tests/evidence/geo314-one-axis-stagger-20261022/ledger-c4aad5d7/FIX_PROOF_INDEX.md)
- [runner 原 M110 真三態自證](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/tests/evidence/geo314-one-axis-stagger-20261022/ledger-c4aad5d7/real-equivalence-proof/README.md)
- [ASM anchor 原三方法三態自證](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/tests/evidence/geo314-one-axis-stagger-20261022/ledger-c4aad5d7/real-assembly-anchor-proof/README.md)
- [L 的 Linux 架構四檔與原三裁判](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/tests/evidence/geo314-one-axis-stagger-20261022/architecture-5c2c5dbd/PROGRESS.md)
- [固定 F 的逐項進度](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/PROGRESS.md)
- [固定 F 完整 ASM 原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/receipts/assembly-final.json)
- [固定 F 三架構原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/receipts/architecture-final.json)
- [正式驗收摘要](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/FORMAL_SUMMARY.md)
- [七項原結果索引](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/ORIGINAL_RESULT_INDEX.json)
- [純整理 metrics](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/FORMAL_METRICS.json)
- [完整來源角色與原 raw 索引](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/SOURCE_HANDOFF.json)
- [P73 引文範圍精確化紀錄](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/EDITORIAL_UPDATE.json)
- [完整原始封包與逐檔 inventory](https://github.com/ZhiQiYang/geometry-axiom/tree/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/raw)

已公開封包附逐檔 inventory、bytes、SHA-256 與原 argv／退出碼／stdout／stderr／環境／SHA；原完整七項終態、outer、各發布 streams 與修復均逐 member 解包驗同。`FORMAL_METRICS.json` 與 scope 索引是純整理，metrics 收錄時 caution 為 0；整理器成功退出不當成新的驗收裁判。原 core 工具未另存逐次內層 stdout 的部分，只引用其原 structured outcome 與 hash，不補造不存在的原 streams。

## 最不確定的地方

本輪已在固定 F 完成原 native、六 browser、完整 ASM 與三架構，驗收範圍按上述原 job／scope 界定。Linux 原允許的 Windows GDI skip 1 照列，沒有動態執行 Windows GDI／MSVC；此 #314 分支也未與 #323 或 #299＋#316 combined 補丁疊合驗收。舊 S 的生命週期唯讀審查未重現漏接，但混合 `parameter-package` Q3、超過起始容量的 facts／realloc／OOM、確認後段逐分支故障及完整 P177 全域動態計數，不能從靜態接線或既有 generation 斷言推成已測過；最終結果須以實際 F 收據界定範圍。

來源分支為 `codex/geo314-one-axis-stagger-20261022`，正文分支為 `codex/geo314-one-axis-stagger-20261022-prbody`，後者僅含 `PR_BODY.md`。較早 E 保留歷史公開快照，最終 E 只保存固定 F 的證據；沒有合併、force push 或修改公理層／決策佇列。GitHub API 存取受限，線上 PR #314 的正文尚未套用；請以此檔更新正文，base 依 handoff 保持在整合分支，合併仍等待 #288 進 main。
