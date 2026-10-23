# #323：同步 #288 最終產品來源，修復載入殘餘成本

本 PR 保留成功的 member／pose／footprint 讀取快取，每個 consumer 仍登記原 dependency kind 與順序。已普通 merge #288 最終產品來源，保留輕量 contact decoder、失敗 prefix completion 與 deferred raw snapshot 契約；沒有 rebase、force push、合併 PR，沒有改公理／決策原文、斷言或數值門檻。

**目前仍阻擋合併。** 新基線 N64 已達原 ≤1.3 門檻；N32 原不得變慢條件與來源呼叫成長條件仍紅，兩個測試負控制也已查明失準。完整 native 正在原程序執行，先收齊這輪全部紅燈，再一次修正。以下不把草稿或未終態項寫成通過。

## 唯一 current-state 矩陣

| 角色／關卡 | 綁定來源／原退出 | 目前結果與 scope |
|---|---|---|
| 受驗產品／測試基線 S | `b2445b5a270d60fdf48b07f6edddbe91266d8aa2` | 已一般 push、遠端同 SHA；受驗前後 clean |
| 普通 merge 兩親 | own `307a18ec5972619161a59df82dcb7e765d137c90`；integration `b74f9a2ae7ade1555b9be45283adecc097fb76e3` | merge／commit／push 原 0，無衝突；沒有 rebase |
| 同步的 #288 產品／證據 | F `3d681636902371ecc528b20f51eea33e272581c9`；合入 E `b74f9a2a…` | F 到 E 只含 evidence；#288 後續 evidence 不改這個產品 closure |
| 比較基底／main | base `b74f9a2ae7ade1555b9be45283adecc097fb76e3`；main `adbaebf9c73ea6801d7b4d5214e4b846b132923b` | 原 v3 各 stage 固定同一組，不換 main 分母 |
| 本輪 evidence head | 尚未產生 | 新 raw 保存於雲端外部目錄，整輪結束後封存；舊 E `307a18ec…` 只屬 S5c 同步準備，不能替代新證據 |
| 最終修正產品 F | 尚未固定 | memo／測試控制草稿未套、未編譯、未量測，不宣稱收益 |
| 原三套診斷 | primary／reaper／outer `1/1/1` | PARTIAL：load 11/13、host-facts 22/22、contact 15/15；共 48 pass／2 fail／0 skip |
| v3 prepare／build／compare | 各 stage execution `0/0/0` | 175 scenes 的完整 stdout、有序 graph、guard counters 三方等價 |
| 原 36 筆交錯性能 | stage execution `0`；quantitative 有紅 | N64 fix/main `1.160861952340483 ≤1.3` 綠；N16/base `0.7020541681432466`、N48/base `0.7354720650542408` 綠；N32/base `1.0008656473515014 >1.0` 紅。無重抽／容差 |
| 原四次 gprof | stage execution `0`；calls gate 紅 | fix N32／N64 source calls `169688/1044429`；64/32 `6.154996228372071 >4.5` 紅 |
| 原必要八套 | stage execution `1` | PARTIAL：675 項，673 pass／2 fail／0 skip；只有下述相同兩個控制失準 |
| 原完整 PF3 | stage execution `0` | baseline20、19 mutants 各正常 killed/exit1、restored20；0 error／skip，originalSourcesUnchanged=true |
| 原完整 native | 尚未終態／exit `null` | 14:30:38 UTC 開始原 225 suites；`ulimit -s 16384; python3 tests/run_all.py --build`，不縮範圍、不重開；本段 build 如實 reused 同 S／fingerprint fresh binaries |
| v3 完整驗收 | 尚未終態 | 已完成 stage 的 wrapper 原 `1`；stage 成功不等於量化 acceptance 全綠 |
| mutate check／帳本 | final source 尚未固定 | 最後由 root 統一 check、必要時整份重產；incoming／歷史帳本不冒 fresh |
| 架構三條／四檔收據 | final source 尚未固定 | incoming 四檔保原 provenance；最後 closure 統一刷新與重驗 |
| 對抗審查 | 本輪動態／公開包尚未結案 | S5c 靜審完成；memo v2、testfix v1、合併草稿分別靜審 52／48／54 checks，皆 0 findings，沒有動態綠燈聲明 |
| 允許 skip | 已終態項 0 skip；native 待原結果 | 只接受原具名 Windows GDI allowlist，不新增環境豁免 |

原 v3 driver 為 `/tmp/geo323-merge-20261023/acceptance-tools-v3/run.py`；各 stage 各一次，精確 argv 的共同部分：

```sh
python3 -B /tmp/geo323-merge-20261023/acceptance-tools-v3/run.py --repo /tmp/g261-next323 --sha b2445b5a270d60fdf48b07f6edddbe91266d8aa2 --base b74f9a2ae7ade1555b9be45283adecc097fb76e3 --main adbaebf9c73ea6801d7b4d5214e4b846b132923b --out /tmp/geo323-baseline-b2445b5a-v3-r1 --heavy-lock /tmp/g261r3/heavy.lock --stage <prepare|build|compare|perf|profile|required-eight|pf3|native>
```

三套診斷使用原 `tests/run_all.py --build --only py:test_geo261_load_residual --only py:test_geo261_host_facts_authority --only py:test_geo261_contact_sources`。原 c387 capture、reaper、16 MiB stack、完整 argv／環境／stdout／stderr／exit／hash／clean SHA 守門保留。perf／profile 原 36＋4 程序已在獨占窗口完成，未重抽；PF3／native 保原 R3 與 timeout。兩個 PARTIAL 不冒完整 native。

## 最新審查與本輪紅燈

最新已讀 #323 審查是 handoff `handoff/pr-reviews/323.md` 的 2026-10-23 08:37:05 UTC、head `307a18e`，取自 handoff `acd1289228d490c68a139cf17e02fdc1f3cb247c`。已同步 #288 final 產品並重驗新 S；仍保留原 ≤1.3 gate，沒有移交或縮限到 #300。歷史 f43 的 `1.7457212386` 紅保原 provenance，不能當新 S 的 N64 結果。

- cross-consumer 舊負控只撤 H 三個 depend site；輕量 contact 經 W reader 仍登記 placement edge，實際先出 footprint marker，與原 placement marker 不符。候選精準撤 second consumer 的 placement 語意邊界，保留原 `ASSERT:cross-consumer-placement-edge-missing`。
- footprint-order 舊注入以 header 物件呼叫 full definition API，導致編譯錯誤。候選只換成相同 source／kind 的 `geo_placement_sources_definition_header`，保原 early-read 故障與有序 edge oracle；編譯失敗不算 kill。
- 新 profile 的三欄 contact reader 每次仍呼叫一次 `geo_eval_source`，提供 calls 成長紅燈的具體熱路徑。外部四檔草稿只快取成功三欄解碼，使用獨立 id key 與原 owner/reset 生命週期；每個 hit 仍登記當前 consumer 的原 placement dependency。原 decoder、格式驗證、失敗與 sealed 路徑保留，並加 contact-hit edge／kind／order 與 contact-id 各具名反證。合併草稿 patch `a44018ad1e3455af89dc9fbc19ea4ec3d9b0e4dfec56f9ddab5d2893d91871b0` 未套／未測，收益未知。

## 原件、環境與限制

新原件位於 `/tmp/geo323-baseline-b2445b5a-three/`、`/tmp/geo323-baseline-b2445b5a-v3-r1/` 及兩個 outer launch 目錄。native 尚在執行，受驗 HEAD 維持 S clean；凍結整輪後才提交 own evidence，不提前移動受驗 HEAD。後續正常 push，不使用使用者電腦。

磁碟維護保留本輪 source／raw／性能樣本。普通 merge 的 `205298659` bytes 完整 diff stdout 也保留，後續用 lossless 分塊與重建 hash 封存，不當 cache 排除。

歷史 S5c 準備證據見 [E307a18ec 的 PROGRESS.md](https://github.com/ZhiQiYang/geometry-axiom/blob/307a18ec5972619161a59df82dcb7e765d137c90/tests/evidence/geo261-load-residual-20261023/postmerge-5c29eba3/PROGRESS.md)；歷史 f43 完整收據在 `tests/evidence/geo261-load-residual-20261022/final-f43e8d8b/`。兩者均不外推新 S 綠燈。

最不確定的是草稿對 N32／source-call gate 的實際收益，以及 native 尚未收齊的其他紅燈。先跑完這輪，再集中修正、做真具名撤回反證並在新可解析 SHA 重驗；不改原門檻。
