柱／樑 native snapshot 缺少或損壞 `faces` 時，公開 evaluate 路徑回傳既有 `UNSUPPORTED / BASE_SOURCE_BINDING / I32 / Native box source faces disagree with legacy provenance.`，避免未分類例外。本 PR 是 #324 的 Codex 接替線。

固定產品來源 F 已重跑指定九個 importer module **142／142、零失敗／零略過**，並完成 list／dict／feature 三組原 `0/1/0`。**正式 11 個整合項仍為 3 PASS／1 RED／7 UNRUN**；完整 native／expected、六 browser 與帳本尚未收斂，維持 draft。

| 來源角色 | 完整 SHA／分支 |
|---|---|
| 產品與本輪 142／三組反證 execution F | `38da31bcac91db631e6325e40b228f8604810e82` |
| 本輪 evidence head E | `EVIDENCE_HEAD_PLACEHOLDER` |
| 既有架構三條／帳本 check execution M | `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` |
| 歷史 importer／反證 execution S | `57b680140da2c6b77ab0d362a72029d8d7c9334b`（只保歷史） |
| 已普通 merge 的 #340 source | `4d3a17c306cad42057589c5cfd964f1c32b755c4` |
| source／body branch | `codex/geo324-faces-20261024`／`codex/geo324-faces-20261024-prbody` |
| PR base | `codex/kernel-without-woodworking-20261023`（#340，仍未驗收 draft） |

以下是唯一 current-state 矩陣。標「正式」的 11 列計入前述整合統計；指定 importer／反證與 registry discovery 另列原實際範圍。`null` 表示未跑，不是 skip；本輪沒有新增允許的 skip。

| Gate | 範圍／目前結果 | 原 exit | execution SHA |
|---|---|---|---|
| native-and-full-expected | 正式／UNRUN | `null` | `null` |
| canvas | 正式／UNRUN | `null` | `null` |
| assembly | 正式／UNRUN | `null` | `null` |
| documents | 正式／UNRUN | `null` | `null` |
| grid | 正式／UNRUN | `null` | `null` |
| space | 正式／UNRUN | `null` | `null` |
| timber | 正式／UNRUN | `null` | `null` |
| mutation-check | 正式／RED：123 定義、110 紀錄；107 stale、3 retired、13 unrun | `1` | `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` |
| architecture-contract | 正式／PASS：604 inputs、798 edges、0 diagnostics | `0` | `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` |
| architecture-tests | 正式／PASS：205 原方法、0 skip | `0` | `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` |
| product-architecture-tests | 正式／PASS：18 原方法、0 skip | `0` | `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` |
| affected-importers | 指定九 module／PASS：142 實跑／通過、0 fail／skip；非 aggregate | 九個原 runner 各 `0` | `38da31bcac91db631e6325e40b228f8604810e82` |
| predicate-list | PASS：原正常斷言撤回／恢復、原碼 bytes 還原 | `0/1/0` | `38da31bcac91db631e6325e40b228f8604810e82` |
| predicate-dict | PASS：原正常斷言撤回／恢復、原碼 bytes 還原 | `0/1/0` | `38da31bcac91db631e6325e40b228f8604810e82` |
| predicate-feature | PASS：原正常斷言撤回／恢復、原碼 bytes 還原 | `0/1/0` | `38da31bcac91db631e6325e40b228f8604810e82` |
| registry-list | 原 discovery 清點，不代 expected gate | `0` | `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` |

142 的九個原 module 為 host_sources45、source_runtime10、kernel_runtime10、rectangular_python9、host_world8、kernel_compatibility1、domain_source_pins16、host_native30、default_native13；全部用原 `_unittest_runner.py` 執行，沒有使用準備版 `run_all --only` 代替 aggregate。native43 的原 fallback／private bridge 與 model-base 編譯均退出 0；493 個原 Git inputs、logical stage、HEAD 與乾淨工作區初末一致。三組反證各保 baseline／withdraw／restored 的命令與原退出碼；withdraw 都是具名正常 AssertionError，分別揭露 null faces 的 TypeError、nested-list face 的 AttributeError、list feature 的 TypeError，未把 crash 或編譯錯誤算作成功反證。原斷言、golden、各層時限均未放寬。

本輪原件位於 `evidence/geo339-final-F38da/`。原件包 `raw/ORIGINAL_F38DA_IMPORTERS_142_AND_PREDICATE_PROOFS.tar.gz` 為 4,716,492 bytes／1,469 members，SHA-256 `c2d2c75b39536d7e801cb31af2cc49d0de3aafd130a0a0cdd27b6701b8abc435`；完整暴露的 stdout／stderr、環境、SHA、原工具與 Git blob 均保存，另保兩支 ELF 的 sidecar／hash，原 ELF 留在雲端未刪。獨立實績審查 6,636 項／0 finding。原工具未公開的內部 pipe 不另補造。

M→F 只更新架構 report／receipt 兩個非執行性衍生檔，604 架構 executable inputs 與三個原 judge bytes 相同；表內仍忠實記 execution M。既有 Linux manifest／scan／report／receipt 與 manifest digest 原 `0/1/0` 保在 `evidence/geo339-final-1f0ebd3e/`。帳本原紅與完整整合未跑不因本輪 142／三反證而變綠；沒有編輯或重產帳本，不借用尚未包含本線的 #338 L 收據。

最新已讀審查是 fresh fetch 的 handoff `1ddb1bb73b9bc0958cf488280412ba116c880a5e` 中 `handoff/pr-reviews/339.md`，2026-10-24 00:39:36 UTC／head `e9ee6d0`：B3 的 142 importer／三 predicate 部分已有同 F 新實績，aggregate native 仍 UNRUN，故 B3 尚未完全解除；B1 的完整正式清單仍未完成。

B2：最新審查所列 Actions [40040764499](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/40040764499) 七 required jobs 仍 failure，runner 空、steps 空。沒有宣稱已修帳戶／支出設定、已重跑 CI 或取得同 head 接受證據；舊 run 的 annotations 不當作新 run 的原因證據。這些 failure 不算產品 pass 或允許的 skip。

C1：#339 是唯一 Codex 接替 owner，舊 #324 凍結；可見 PR／issue 的正式重導向或關閉仍須完成，不以 evidence 自述冒充已完成。C2：base #340 仍未驗收，待主代理按普通 merge 收斂穩定基底，對最終組合來源重核受影響範圍。沒有 rebase、force push、合併 PR，沒有修改公理或決策佇列。

下一步是最終來源的完整帳本、完整 native／expected 與六 browser，沿用原 workflow 時限與 golden；本 PR 尚未標 READY-TO-MERGE。舊 `evidence/geo324-final-57b68014/` 與 `evidence/geo339-review-followup-F38da/` 僅保歷史，不作第二份 current-state 矩陣。
