# M11：將過時錨點遷移到現行精確孔中心守門

修正來源為 `9a6b88005aa364d2b6b9f1710a519c6710017154`，分支 `codex/geo261-fix-m11-live-anchor-20261018`，基底為 integration `e9c1509cf89e6f35d298743ec5e3368370316cf7`。分類：**預期過時，mutation 定義未承接既有精確幾何修正**。只修改 `tests/mutate.py` 的 M11 `desc/old/new` 三欄；產品守門、M11 身分、其他 mutant、全部測試斷言、migration pin、版本化 ledger 與 census 均未改。

正式單筆 M11 已真執行：未變異基準 **157/157**；mutant 完整 157 個案例為 **148 pass／9 fail／0 infrastructure**，判定 killed。修前與撤回時，同一 migration 方法都因 M11 錨點失效轉紅，CLI 都明確 INVALID；修後與恢復的三模組回歸各 **55/55、零 skip**。這是單題證據，**不代表全表 mutation 或整合驗收通過**。

## 根因與最小修正

`0b64623b72c21bd7f348d0fc292541ff1dfb66db` 修正單位孔包含漏洞後，舊 `inside == 4` 判式已不存在；後續 owner 遷移 `6bddee15ad12b8a2dc0d4c6024988ffab0569d2d` 仍保留舊 M11 字串。修前完整錨點出現 0 次，現行中心判式完整錨點恰 1 次。

SSOT I5（固定來源 `公理層.md:1135–1142`）要求整個閉矩形包含於有效區域、檢查所有孔，單純貼邊仍合法。現 `geometry-core/kernel/geometry.c:560–565` 在孔邊未穿入矩形開內部後，用精確雙倍座標中心判斷孔完全罩住矩形。M11 改為只停用這道拒絕的 `if (0 && geo_loop_rect_center_inside(...))`，保留 marker `GEO261_HOLE_RECT_CENTER`。沒有還原舊算法、放寬產品 I5 或將 M11 退休／標等價。

[真修正提交 patch](patches/fix.patch) 與 [只撤三欄的本地控制 patch](patches/withdraw.patch) 均來自固定 Git 物件。控制 `a24ac250855e6ec9abd8e16dd6e61564c2e66e2b` 的整個 tree 等於基底 e9；控制未列為要合併的修正。

## 實際執行結果

表中的 unittest 秒數取原 footer；命令總秒數另由 recorder 記錄，不混作同一計時。

| 階段 | SHA | 結果 | unittest 秒 | 命令總秒 |
| --- | --- | --- | ---: | ---: |
| 修前 migration | e9c1509c | 1 方法，M11 subTest failure | 3.285 | 3.512 |
| 修前正式 M11 CLI | e9c1509c | 1 筆 INVALID，錨點 0 次，exit 1 | — | 0.215 |
| 修後三模組回歸 | 9a6b8800 | 55/55，零 skip/error | 13.702 | 13.964 |
| 正式 M11 CLI | 9a6b8800 | baseline 157/157；mutant 148 pass、9 fail、0 infrastructure；killed | — | 82.242 |
| 單筆正式 freshness | 9a6b8800 | M11 killed，stale/blocked 0；exit 0 | — | 0.265 |
| 另次 baseline raw oracle | 9a6b8800 | 157/157，exit 0 | — | 22.944 |
| 另次 mutant raw oracle | 9a6b8800 | 148 pass、9 fail、0 infrastructure；exit 1 | — | 22.469 |
| 撤回 migration | a24ac250 | 同一 1 方法／M11 subTest failure | 3.771 | 4.089 |
| 撤回正式 M11 CLI | a24ac250 | 同一錨點 0 次 INVALID，exit 1 | — | 0.264 |
| 恢復三模組回歸 | 9a6b8800 | 55/55，零 skip/error | 14.033 | 14.244 |
| 恢復後單筆 freshness | 9a6b8800 | 原 M11 收據仍 killed/fresh；exit 0 | — | 0.215 |

三個回歸模組為 mutation migration 15、mutation freshness 32、region edges 8，共 55。兩次 migration 紅燈均為原 `self.assertEqual("equivalent" if m.get("equivalent") else "run", kind)` 得到 `'run' != 'invalid'`；不是方法缺失、import/setup、編譯失敗、timeout 或 crash。兩次 CLI INVALID 都在錨點檢查時停止，**沒有跑產品 oracle，不能算產品 kill**。

所有 stage 的 argv、head、raw stdout/stderr、source/head/status 穩定觀測見 [results.json](results.json) 與各 stage 原收據。[人工台帳](manual-ledger.json) 分開記錄原生案例數、unittest 方法數與 freshness 檢查，沒有將 CLI exit 0 自動當測試全綠。

## 正式 M11 實際殺手與證據界線

正式工具執行一次未變異 oracle及一次 mutant oracle；兩個 structured result 都恰有 157 個唯一場景，順序逐項等於來源 9a 的 `run_tests.TESTS`，退出碼與結果計數一致。首個 mutant 失敗原文為：

```text
_test_hole_auto.scene: FAIL 應接受但拒絕: <repo>/_test_hole_auto.scene:15: V_CUT_PRIORITY：角材 2 端面頂到外輪廓邊（RC）——那條邊還沒鋪邊界材；只有 boundary 可頂 RC
```

這是停用中心 guard 後，既有合法場景由 baseline pass 轉成拒絕；**不是本次正式 oracle 直接觀測「孔內非法矩形被接受」**。沒有逐步 trace 可把九個下游失敗再細分成額外根因，報告保留原 assertion／diagnostic。

九個失敗場景全部保存在 [正式 M11 JSON](mutation-results/after-M11.json)：`_test_hole_auto.scene`、`_test_ambiguous.scene`、`_demo_ceiling.scene`、`_edge_upper_seg.scene`、`_mut_reval_free_hole.scene`、`_mut_through_boundary.scene`、`_mut_free_hole_end.scene`、`_wit_r6_span_cells.scene`、`_ax_i5_hole_vertex_touches_rect_edge.scene`。工具 `KILLED_BY_MAX=5`，所以 `killed_by` 只列前五個，不代表只有五個失敗。

另有原 region_edges 的 `test_removing_hole_center_guard_breaks_kernel_strips_and_product`（第 91–105 行）：它以 `if (0)` 停用同一中心守門，驗 K rectangles/strips 紅、真 bridge 錯誤接受且 dump 改變，再恢復正控制。此方法在兩輪 55 中通過，斷言完整保留；它與正式 M11 157 場景是不同執行路徑，不能冒作正式 M11 的首個殺手，也不宣稱有另外保存這個方法內所有 transient child raw。

## 原工具收據與後續 raw 執行

`mutate.py` 內部 oracle 只保存完整 structured result 與 stdout/stderr 的 decoded/reencoded SHA，沒有將當次完整文字 streams 落檔。[after-m11 原 stdout](after-m11/command.stdout) 是 mutation 工具外層輸出，不是其內部兩次 oracle 的完整 raw。

為補可直接閱讀的原 oracle 輸出，之後用同一兩支保留 binary 分別另跑 `python3 -B tests/run_tests.py <binary>`，保存 [baseline raw](oracle-baseline-raw/command.stdout) 與 [mutant raw](oracle-mutant-raw/command.stdout)。這是**後續另次真執行**。兩份 raw stdout 的 SHA 恰與原工具各自保存的 stdout_sha256 相同，stderr 都空；structured result 按原工具的 `<repo>` 路徑格式比較也全等。這項一致性不改變它們是不同次執行的事實。

正式單筆 [check_pass 輸出](after-m11-freshness/command.stdout) 與 [恢復後重核](restored-m11-freshness/command.stdout) 都只對 M11 收據核新鮮度，不重新編譯或執行 native；最後重核也不是另一輪 M11 kill。CLI 沒有 `--check M11`，這裡使用原 `check_pass([M11], killers=True)`，不冒稱全表 strict check。

## Binary、來源與公開範圍

正式工具明列 baseline 與 M11 都「已重編」，compile exit 0，命令為 `cc -std=c11 -O2 <source> -o <output> -lm`。兩支實際 ELF、sidecar 與工具 execution 收據逐 hash 相符；額外 raw 執行的前後 bytes 身分不變：

| 真執行檔 | bytes | SHA-256 |
| --- | ---: | --- |
| baseline.exe | 869120 | `0c13c9e0e2c2037d899bbeb735afde2bbfb6d8e8eb186e4ddb3f13f868ba7ea9` |
| M11/_mut.exe | 869056 | `73454b0358b7f09d9a129515ebe86806a72d8a87232d857d07552f13c1a80638` |

正式 [M11 結果 JSON](mutation-results/after-M11.json) 為 52252 bytes，SHA-256 `4a12c2c564df026cf2cb0f0b2f4023f552ef772324a4488bbf6097946a81a44b`；兩次 freshness 都沒有改它。record checksum、工具 hash、編譯／來源閉包與 sidecar 核對有對應原收據。一般 `before/after.binaries.json` 另記錄當時 registry 的其他 binary，可能顯示 stale；它們不是這次 M11 執行檔，不能用來替換本次明確 cache／artifact 身分。

公開集合以 [inventory.json](inventory.json) 為準，含原收據、raw、三份外部結果 JSON、捕獲的 fingerprint JSON、真 Git patch 與人工判讀；**不發布 ELF、工具原碼或大型 before/after.source.json**，也不改名繞過。ELF 與完整來源快照留在外部原路徑；公開 payload 不能自行重算未公開的完整 source 清單，source_stable 是原 recorder 的觀測。原 receipt 可能列出未公開 ELF artifact 的檔名／身份，這不表示 ELF 已包含在公開集合。

本題所有 `MUTATE_RESULTS` 都指外部獨立檔，cache 也獨立；原版本化 `tests/mutants_results.json`、`run_all.expected.json` 沒改。工具暫生的 `_mutant_M11.c` 按既有 finally 清理；沒有修改 current_geometry.c 或 kernel 來源。

## 環境與仍未驗的範圍

Debian GNU/Linux 13.6（trixie）、Linux 6.18.55 x86_64、GCC 14.2.0、Python 3.12.14、Node v24.19.0、Google Chrome 155.0.8059.84；child stack 16 MiB。本題沒有執行瀏覽器，版本來自原 recorder 的版本探針。

M11 定義變動會改整份 mutation tool hash；其他舊收據不能因本題單筆成功而沿用。最終同來源仍要完整重跑 **54 個 core（含 4 equivalent）＋10 bridge＝64 項**，另核 3 retired，且完整 strict census／全量非瀏覽器／六 browser／其他未合修正均不在本題完成聲明內。真收據保存到只有 evidence／合法 ledger 輸出的後續 commit 時，execution.head 保留實際執行的 9a，不自改成報告 commit；若產品、工具或 oracle bytes 改變則仍須重驗。

Native18 的「11 套」另有四個未具名入口待 Claude 補齊；本題未用相鄰 suite 或歷史 60/60 代填。沒有合併任何 PR，公開與推送狀態由主代理另行確認。

