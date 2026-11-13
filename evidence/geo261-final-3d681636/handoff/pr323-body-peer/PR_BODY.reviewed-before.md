# #323：#288 final 來源同步後的完整基線與交接

已普通 merge #288 的最終產品來源，保留輕量 contact decoder、逐 consumer 的 dependency kind／順序與 deferred raw snapshot 契約。本輪原八 stage 已全部結案；**驗收仍紅，不能合併**。依使用者最新要求階段性停止，已封存、普通 push 與交接，沒有套候選或開新修正／測試。

## 唯一 current-state 矩陣

| 角色／關卡 | 來源／原退出 | 結果與 scope |
|---|---|---|
| 受驗產品／測試 S | `b2445b5a270d60fdf48b07f6edddbe91266d8aa2` | 可解析；原八 stage 前後均 clean。沒有新的產品／tests 修改 |
| evidence head E | `4ea6c50796711ed1e79bae89c93d07037d317837` | 已普通 push、遠端同 SHA；S→E 唯一變更是 `evidence/geo323-final-b2445b5a/` |
| merge 兩親／base | own `307a18ec5972619161a59df82dcb7e765d137c90`；integration/base `b74f9a2ae7ade1555b9be45283adecc097fb76e3` | 普通 merge 無衝突；base 包含 #288 產品 F `3d681636902371ecc528b20f51eea33e272581c9`，F→base 只含 evidence |
| 原 main 比較分母 | `adbaebf9c73ea6801d7b4d5214e4b846b132923b` | 原 protocol 固定，不換分母 |
| 原三套診斷 | primary／reaper／outer `1/1/1` | PARTIAL：load11/13、host22/22、contact15/15；48pass/2fail/0skip |
| v3 prepare／build／compare | stage execution `0/0/0` | 175場景完整stdout、有序graph與guard counters三方等價 |
| 原36筆交錯性能 | stage execution `0`；quantitative 有紅 | N64/main `1.160861952340483≤1.3` 綠；N16/base `0.7020541681432466`、N48/base `0.7354720650542408` 綠；N32/base `1.0008656473515014>1.0` 紅 |
| 原4次gprof | stage execution `0`；calls gate 紅 | fix N32/N64 source calls `169688/1044429`；64/32 `6.154996228372071>4.5` 紅 |
| 原必要八套 | stage execution `1` | PARTIAL：675項、673pass/2fail/0skip；相同兩個load控制失準 |
| 原完整PF3 | stage execution `0` | baseline20、19具名mutants各正常killed/exit1、restored20；0error/skip，originalSourcesUnchanged=true |
| 原完整native | 原run_all／stage execution `1/1` | 225suites、5200pass/2fail/1具名允許skip；另外不納測試數的mutation:check因STALE為FAIL。15:01:42 UTC真終態 |
| 原完整v3判決 | wrapper `1`；full_acceptance `false` | 八stage全部completed，保全部量化／測試紅燈；PF3原0不因累積wrapper1誤標紅 |
| 帳本 | native內原`mutation:check` exit `1` | closure過期；沒有整份重產。依root規則在最終stack統一重產，不冒fresh |
| final架構三條／四檔收據 | 尚未開始新的final closure刷新 | native內相關unittest仍屬native原scope；不把incoming四檔宣稱對未來修正fresh |
| 未套四檔候選／反證 | 新控制、新三套與新final v3均未執行 | patch `a44018ad…`；產品兩檔、測試兩檔，保13方法；獨立靜審54checks/0findings，收益未知 |
| 出版／公開範圍 | 封存器`0`、普通push/ls-remote`0` | 6包229482052bytes／14138members；producer核6個Git blobs、7036原streams/metadata全同，53可重建項明列、原stdout/stderr排除0。獨立公開包peer尚未做 |
| 最外scheduler收尾 | TOP RESULT缺失、最外console exit未知 | UI傳輸失效後PID已殭屍；原八stage及內層實exit/streams已存，不推定scheduler成功、不重跑／補造原件 |
| 允許skip | 原Windows GDI harness `1` | 原具名allowlist；其他已終態項0skip，沒有新增豁免 |
| 本輪未跑browser | #323六browser未啟動 | 階段性停止後未開始，不是本環境缺Chrome，不借#288綠燈冒#323新結果 |

正式基線均綁定 S。merge準備與base/main子程序保原SHA／角色，不把歷史或比較來源改標成fix。沒有rebase、force push、PR合併、SSOT／決策原文修改或門檻放寬。

## 原命令與原紅燈

原 v3 每個 stage 各一次，完整 argv／環境／stdout／stderr／exit／hash 在包內：

```sh
python3 -B /tmp/geo323-merge-20261023/acceptance-tools-v3/run.py --repo /tmp/g261-next323 --sha b2445b5a270d60fdf48b07f6edddbe91266d8aa2 --base b74f9a2ae7ade1555b9be45283adecc097fb76e3 --main adbaebf9c73ea6801d7b4d5214e4b846b132923b --out /tmp/geo323-baseline-b2445b5a-v3-r1 --heavy-lock /tmp/g261r3/heavy.lock --stage <prepare|build|compare|perf|profile|required-eight|pf3|native>
```

native為原`ulimit -s 16384; python3 tests/run_all.py --build`完整清單；原`--build`如實reused同S／fingerprint fresh binaries。原三套是`--only py:test_geo261_load_residual --only py:test_geo261_host_facts_authority --only py:test_geo261_contact_sources`。原c387、reaper、16MiB stack、R3、timeout與13/22/15計數不變；36timings與4gprof一次在獨占窗口執行，未重抽。

兩個test-control drift保原失敗與精確marker：

- cross-consumer舊控制只撤H三個depend site，未撤新版W contact reader的placement edge；實際先出footprint marker，原測試仍要求`ASSERT:cross-consumer-placement-edge-missing`。未改expectation規避。
- footprint-order舊注入傳header物件給full definition API，編譯錯誤不算mutation kill。候選只換成同source／kind的`geo_placement_sources_definition_header`，保原early-read與ordered-edge oracle。

N32微小紅與source-call成長紅都保留，不加容差。新profile指向每次輕量contact decode仍一次`geo_eval_source`的熱路徑；舊f43的N64 `1.7457212386`只保歷史provenance，不當本輪N64數字。

## 公開交接與停止點

入口：[PROGRESS.md](https://github.com/ZhiQiYang/geometry-axiom/blob/4ea6c50796711ed1e79bae89c93d07037d317837/evidence/geo323-final-b2445b5a/PROGRESS.md)、[HANDOFF.md](https://github.com/ZhiQiYang/geometry-axiom/blob/4ea6c50796711ed1e79bae89c93d07037d317837/evidence/geo323-final-b2445b5a/HANDOFF.md)、[BASELINE_CURRENT_SUMMARY.json](https://github.com/ZhiQiYang/geometry-axiom/blob/4ea6c50796711ed1e79bae89c93d07037d317837/evidence/geo323-final-b2445b5a/BASELINE_CURRENT_SUMMARY.json)、[RECOVERY.json](https://github.com/ZhiQiYang/geometry-axiom/blob/4ea6c50796711ed1e79bae89c93d07037d317837/evidence/geo323-final-b2445b5a/RECOVERY.json)。原完整raw在同prefix的`raw/`，未刪雲端原件。

205298659bytes merge stdout保原件，以4獨立gzip raw ranges／精確map無損公開，解壓串接SHA256仍`778f023db9aba56fa84bd85b8ff32c016aec5bb0d9470b445653b0bd3989e174`。出版收尾曾把原stderr與patch空白context套入廣泛whitespace check而exit2，原失敗照存；續封僅核新文案排版0，沒有trim原raw、改patch或改產品assert。

未套候選的[patch與manifest](https://github.com/ZhiQiYang/geometry-axiom/tree/4ea6c50796711ed1e79bae89c93d07037d317837/evidence/geo323-final-b2445b5a/unapplied-candidate)已公開：patch SHA256 `a44018ad1e3455af89dc9fbc19ea4ec3d9b0e4dfec56f9ddab5d2893d91871b0`。它只cache成功的contact三欄，每hit仍發當前consumer原placement depend，獨立id／owner-reset守門；新增contact-hit edge/kind/order/id各具名反證。真0/1/0、failed/sealed/lifecycle動態與性能收益全未驗。prepared-only修後三套launcher與14項獨立靜審也在包內，沒有執行。

最後已讀#323審查：handoff `acd1289228d490c68a139cf17e02fdc1f3cb247c` 的`handoff/pr-reviews/323.md`，2026-10-23 08:37:05 UTC／head307a18e。仍保≤1.3本PR gate，不移交#300縮限；後續需root安排318→314→combined後的forward merge／final closure。木工推理前讀最新main決策佇列與pr333 FIELD-RULES；本輪讀取的原Git bytes/hash已封。

最不確定的是未套memo對N32／calls的實際收益、forward-merge後closure，以及尚未做的獨立公開包peer。接手者從HANDOFF讀原紅，再在新可解析SHA做真反證與完整原驗收。**本階段已停止，不自動續跑。**
