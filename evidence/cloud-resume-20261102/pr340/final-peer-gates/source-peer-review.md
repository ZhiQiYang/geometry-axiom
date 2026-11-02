# #340 final 候選來源同一性與普通合併 peer 核收

核收通過。固定候選為 `b3a248607d7eb68d3167abbb926cf491d9b35a26`，指定 main 為 `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d`，#366 工具來源為 `502a64ff6214dd6060927b7f14643a533536f20d`。已先讀該 checkout 的 `AGENTS.md`。本 peer 只讀來源、Git 物件與既有合併紀錄；沒有跑 gates、產品測試、API、fetch、push、留言或新 CI。

## 完整 Git tree 同一性

- 對指定 main **恰好 21 個新增檔案**，沒有修改／刪除／改 mode：`evidence/geo340-convergence-175cee44/` 的 17 個歷史原件，加上以下四個 #366 工具／文件。
- 排除這 21 個明列新增路徑後，候選與 main 的 **38,671 個完整 Git leaf entry**（path、mode、type、blob OID）逐項全等。故其餘全部產品、測試程式、registry、期望數、歷史 mutation ledger 與 SSOT 均與指定 main 完全相同，不只抽比幾個檔案。
- 投影後兩份完整 tree entry 清單的 SHA-256 同為 `c3e3181489918fc48b3b8f9d2b5ad3f6f87fccb99a12beacb7d9765520f1fba9`。候選完整 tree 共 38,692 entries，清單 SHA-256 為 `b2f6ba389203e9d4493e119c3362a03a5d02c4ce76b1137386594714eceb355c`。
- 十七個歷史 evidence 的 mode/type/blob 均精確等於原 #340 head `04959e04c334ceaf03f865514f76b1cac8ee91f2`；沒有重寫或洗來源。
- checkout 是 sparse checkout，規則排除 `evidence/`、`handoff/`、`feedback/`、`drafts/`。上述證明使用完整 `git ls-tree -r -z` 與物件資料，沒有把未 materialize 的歷史檔案誤認成刪除。審查前後 `git status --porcelain=v1` 空白，`git diff --exit-code HEAD` 為 0。

四個新增工具的 mode/type/blob 均精確等於 #366 新 head `502a64f`，bytes SHA-256 如下：

| 路徑 | SHA-256 |
|---|---|
| `.github/scripts/architecture_evidence.py` | `9899d18b3fb80a750308e2342d8309ca7a2470ec5aab4f977bc3213690b07b5b` |
| `.github/scripts/mutation_evidence.py` | `28ec987f9b66f64bea33eff555f807e144d6f2363f202bce55ab85bd51e912fc` |
| `.github/workflows/mutation-evidence.yml` | `c5d39c10de1df05ff1a582f228b4ee5fb088d0637337dc96c552d993a35d1fdb` |
| `tests/MUTATION-EVIDENCE.md` | `995b07d62b232a8d094ec059da096bbe1eecf8506e27c358fbd64f4221304991` |

## 普通 merge lineage

直接從 commit 物件讀取的 parents：

| Commit | 第一 parent | 第二 parent |
|---|---|---|
| `b3a248607d7eb68d3167abbb926cf491d9b35a26` | `1605a6c27c97c2aa5e6405bddc7d3b31f1fdd965` | `502a64ff6214dd6060927b7f14643a533536f20d` |
| `1605a6c27c97c2aa5e6405bddc7d3b31f1fdd965` | `04959e04c334ceaf03f865514f76b1cac8ee91f2` | `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d` |
| `502a64ff6214dd6060927b7f14643a533536f20d` | `df347537c920b5a51ca157d7886857a7d0547d5b` | `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d` |

`git merge-base --is-ancestor` 對 main、#366 head、1605 及原 #340 head 四者到 b3a 均 exit 0。既有 `merge-main.json`、`merge-verified-tool.json` 的原命令均為 `git merge --no-ff`，exit 0，stdout 為 `Merge made by the 'ort' strategy.`；本地 reflog 也依序記錄兩次普通 ort merge。這證明候選保留原 #340、指定 main 與 #366 的正常祖先關係，沒有本地歷史重寫。本 peer 沒有進行或觀測遠端 push，因此不把本地 graph 證據擴寫成已完成遠端推送或已合併 main。

本地 cached `refs/remotes/origin/main` 仍是指定 `5775a9e9`。本輪依有界要求沒有查 API 或 fetch，未獨立確認遠端 main 是否在此後前進；若主代理 metadata 已發現變更，應另報，不由本 peer 自動更新候選。

## 來源紀律與歷史原件

舊 `original-gates/RESULT.json` 明確 `source_sha=1605a6c27c97c2aa5e6405bddc7d3b31f1fdd965`，其中四個 command 的 source_sha 也都是 1605。候選 b3a 與 1605 相差四個新增工具；**舊 light gates 保留在 1605，不移標為 b3a execution**。此檔 SHA-256 為 `0aa2143f451c90b5d85c415709699d2cc74505c67f27d584ce81fffd6988b071`。b3a 的新 gates 由主核收代理另行執行及保存，本 peer 不代替其結果。

歷史 `AGGREGATE_RESULT.json` 的執行來源仍是 `175cee44c56c89871803d955c0c525236727ba65`，scope 為 selected aggregate、`fullAggregate=false`；`CURRENT_STATE.json`、`MERGE_RESULT.json`、`PUBLICATION_INDEX.json` 仍保留舊 source 及未執行範圍，且 `noOldExecutionShaRelabelled=true`。本輪以相同 Git blob 核收它們是歷史原件，沒有把歷史 selected aggregate、七階段或舊證據寫成 b3a 新 source execution；沒有重新解壓或重審 17 個 archive 的內容。

## 可重核指令、退出碼與 hash

本輪只讀 checker：

```sh
python -B /tmp/geometry-resume-20261102/pr340/final-peer-gates/source_peer_check.py
```

exit 0，`passed=true`，58 項來源／lineage assertions。完整 command argv、每條退出碼及 stdout/stderr SHA-256 皆保存在同目錄 `source-peer-review.json`；其中 29 條 Git 指令全部 exit 0。核心只讀命令包含 `rev-parse`、`status`、`diff --exit-code`、`ls-tree -r -z`、`show --format=%P`、`show <sha>:<path>`、`merge-base --is-ancestor`、`reflog`；沒有呼叫測試或 gate 入口。

| 檔案 | SHA-256 |
|---|---|
| `source_peer_check.py` | `0dad59b2f8b9a395b0f63304196cb5568afad9a9dd18d69a6bd61e371a720403` |
| `source-peer-review.json` | `2bb93f65b4a825a33987b1b5966def4067ae8624f7b1319c20eb099727e5b8b0` |

未驗：遠端最新 main／PR metadata、遠端 push、b3a 測試執行、歷史 archive 內容重審。這些限制不影響本輪已證明的固定 commit 完整 tree／blob 同一性與普通本地 merge lineage。
