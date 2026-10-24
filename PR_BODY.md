柱／樑 native snapshot 缺少或損壞 `faces` 時，公開 evaluate 路徑回傳既有 `UNSUPPORTED / BASE_SOURCE_BINDING / I32 / Native box source faces disagree with legacy provenance.`，避免未分類例外。本 PR 是 #324 的 Codex 接替線。

本次已一般 merge 更新後的 #340，來源 F1 固定為 `616ce7538d23fbe7f3bbefae7f2a04e25ebd75a4`。合併只採入 L 的原帳本與 evidence，沒有手改產品、tests 或裁判。新 F1 的正式 11 項均尚未執行；原 F38da 的 142／三組反證在精確 executable closure 相同下沿用有效實績；execution SHA 仍為 F38da，不改標 F1 新執行。舊 M 的架構／帳本結果保留原 execution SHA。以下是唯一 current-state 矩陣。

| Gate／身份 | 目前結果或來源 | 原 exit | execution SHA |
|---|---|---|---|
| Current product/source F1 | `616ce7538d23fbe7f3bbefae7f2a04e25ebd75a4` | 不適用 | 不適用 |
| Evidence head E | `8f39025be6708bd9d58e576ed5b349b7ef628624` | 不適用 | 不適用 |
| 一般 merge parents | 舊 E `1d94ab77ab29952d5b73ec5b262dfd239819fe25` ＋ 新 #340 `175cee44c56c89871803d955c0c525236727ba65` | merge `0` | 非測試 |
| Source／body branch | `codex/geo324-faces-20261024`／`codex/geo324-faces-20261024-prbody` | 不適用 | 不適用 |
| PR base | `codex/kernel-without-woodworking-20261023`（#340，未驗收 draft） | 不適用 | 不適用 |
| native-and-full-expected | 正式／UNRUN at F1 | `null` | `null` |
| canvas | 正式／UNRUN at F1 | `null` | `null` |
| assembly | 正式／UNRUN at F1 | `null` | `null` |
| documents | 正式／UNRUN at F1 | `null` | `null` |
| grid | 正式／UNRUN at F1 | `null` | `null` |
| space | 正式／UNRUN at F1 | `null` | `null` |
| timber | 正式／UNRUN at F1 | `null` | `null` |
| mutation-check | 正式／UNRUN at F1；L 原 ledger blob 已採入，尚未 check | `null` | `null` |
| architecture-contract | 正式／UNRUN at F1 | `null` | `null` |
| architecture-tests | 正式／UNRUN at F1 | `null` | `null` |
| product-architecture-tests | 正式／UNRUN at F1 | `null` | `null` |
| affected-importers | PASS：原 142／142、0 skip；新 F1 executable closure 全同，沿用原實績，未在 F1 重跑 | 九原 runner 各 `0` | `38da31bcac91db631e6325e40b228f8604810e82` |
| predicate-list／dict／feature | PASS：原三組正常 `0/1/0`，新 F1 executable closure 全同，未在 F1 重跑 | 各 `0/1/0` | `38da31bcac91db631e6325e40b228f8604810e82` |
| merge closure／普通 push | 原 driver `0`；230 項 registry 保留 kernel13／host45，所有 F38da 非 evidence 來源除 ledger 外相同 | `0` | 非測試 |
| 允許 skip／合併狀態 | 無允許 skip；尚未 READY-TO-MERGE | 不適用 | 不適用 |

本次前一個環境 R1 exit 1 是全新 #340 `--no-checkout` worktree 缺 index，原 3,000,230 bytes status 完整保留，沒有刪原檔。R2 先在固定舊 S 執行 read-tree dry-run，再建立該新 index；兩次 ordinary merge／push 均 exit 0，兩 remote head 與新完整 SHA 一致，兩 checkout 的工作樹及 index clean。原 bfb checkout 保持不動。兩分支 ledger 均精確等 L `7af8c5d80d34cb4f49d01ba67deb78a3a6d725db` 的 Git blob `fb470f96399093f6b25b2b2358011d26f3c36898`；這不等於已執行 `mutate.py --check`。本次原件與收斂守門在 `evidence/geo339-convergence-616ce753/`。

歷史實際 execution F `38da31bcac91db631e6325e40b228f8604810e82` 已完成九 module 142／142、零失敗／零略過，以及 list／dict／feature 三組正常 `0/1/0`；不是 aggregate native。九 module 為 host_sources45、source_runtime10、kernel_runtime10、rectangular_python9、host_world8、kernel_compatibility1、domain_source_pins16、host_native30、default_native13。rectangular_python9 與 #340 的 kernel 13 方法是不同項目，不互相替代。三次撤回均有具名正常 AssertionError，原碼 bytes 還原，未放寬斷言、golden 或時限。原包 `evidence/geo339-final-F38da/raw/ORIGINAL_F38DA_IMPORTERS_142_AND_PREDICATE_PROOFS.tar.gz` 為 4,716,492 bytes／1,469 members，SHA-256 `c2d2c75b39536d7e801cb31af2cc49d0de3aafd130a0a0cdd27b6701b8abc435`，獨立 actual 審查 6,636／0。原 ELF 留雲端，已公開 sidecar/hash；原工具未公開的內部 pipe 沒有補造。

歷史 M `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` 的架構三條原 exit 0，mutation-check 原 exit 1（123 定義、110 紀錄，107 stale／3 retired／13 unrun）仍完整保留，並非本次 F1 的實跑結果。604 架構 inputs 與三 judge 的既有來源關係保留；Linux 四檔及原 digest `0/1/0` 位於 `evidence/geo339-final-1f0ebd3e/`。帳本是否在最終組合有效、架構是否需重產，由 root 在最終統一來源實際執行原工具判定；本次沒有自行重產。

最新已讀 handoff `d2ed8e6efe2760ca562ab7d28f4a2ac09a404fd5` 的 `handoff/pr-reviews/339.md`，最後一則仍為 2026-10-24 00:39:36 UTC／head `e9ee6d0`。B1 的完整正式清單仍未完成；B3 指定 F38da 的 142／三刀已由該 F38da 的原實績補齊；本次 493 原 executable／資料 inputs 加 5 個既有 Markdown，共 498 個 path／mode／type／blob／size 在 F38da 與 F1 完全相同，整個非 evidence 差異只有 mutation ledger。因此不為單純帳本更新重跑這些不受影響項目，仍忠實列原 execution F38da；aggregate native 仍未完成，B3 尚未整體解除。

B2：最新 Actions [40040764499](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/40040764499) 綁定 `e9ee6d088b0cad4e3984aa2842a50acc311c2351`，七 required jobs 均 failure、runner 空、steps 空；本輪讀取各 job 的原 annotation 都指出 payment failed **或** spending limit，證明排程未開始，未分辨兩種帳戶原因。環境分類已有本次 run 的新證據，沒有宣稱帳戶／支出設定已修、CI 已重跑或 required gates 已通過。兩次 signed log 下載 Forbidden 是獨立的存取錯誤，不能推論不存在 logs；公開副本只遮蔽簽章參數，完整原值留雲端，其他 bytes 完全保留。安全證據包與 `PUBLIC_REDACTIONS.json` 位於 `evidence/geo339-final-F38da/current-actions/`，封包 SHA-256 `40567a58ce19e563245b109736ee1417a28e8d77308ce0027df19dfc6fd361c8`，獨立審查 114,024／0；65 原讀取是 63 個 exit 0、2 個下載 exit 1，並非 65 個測試。完整 Git tree 比對證明 F→舊 E 的 20 個差異皆為 evidence，所有其他 tracked path／mode／type／blob 相同；只證來源關係，表內 execution SHA 不移標。B2 仍未解除，這些 failure 不算產品 pass 或允許的 skip。

C1：#339 是唯一 Codex 接替 owner，舊 #324 凍結；可見 PR／issue 的正式重導向或關閉仍須完成，不以 evidence 自述冒充已完成。C2：已用普通 merge 收斂 #340 與 L 的來源，base #340 仍未驗收；此來源合流不等於 C2 驗收解除。沒有 rebase、force push、合併 PR，沒有修改公理或決策佇列。

下一步由 root 在最終統一列車處理完整帳本、架構與原 workflow；本線保留原 142／三 predicate 的同 closure 實績，#340 保留新 13／原反證。後續 probe／capacity 等 C 產品合流改變 closure 時，再由原 aggregate 在同一最終來源統一真跑這九個 module，不重複為單純 ledger 合流重跑。舊矩陣只作歷史，不作第二份 current-state；本 PR 維持 draft。

base #340 另在新 S1 `175cee44c56c89871803d955c0c525236727ba65` 真跑原 selected aggregate，13／13、零 fail／skip、strict expected exit 0；此收據仍綁 S1，未改標本 PR 的 F1 執行，也不能代替本線 142／三刀、完整 native 或六 browser。#340 最新審查仍有 B2 required jobs 與 C1 base 收斂邊界待完成，因此本線 C2 不宣稱已解除。

本次 F38da→F1 的精確來源關係原件為 `raw/FACES_CLOSURE_ORIGINALS.tar.gz`，SHA-256 `95ba193c6b8290573d8baf54c115296975adf8710f9fff78397aa5c97bac7b60`；三個原 Git reads 均 exit 0，493 個原 input-plan entries 逐一核同，另完整記錄唯一 ledger 差異。這份是 closure 收據，不是新測試執行。
