# default-owned-replay 實測與語意證據

`68eed6fb0e488003ca0a4d8614a9460a637d979e` 的同輪 normal 測量顯示，cold start + 首次 dump 中位數 **96.630 ms／main 54.108 ms＝1.786×**；常駐 load_scene **51.006 ms／27.506 ms＝1.854×**。正式 `py:test_bridge_integrity` 兩版各 24/24、零 skip；unittest 耗時 **81.171 s／main 38.161 s＝2.127066900763×，仍未達 ≤2×**。代表性 cold／load 指令改善，並不等於完整 suite 或 GEO-261 全部驗收完成。

修正分支為 `codex/geo261-fix-perf-default-replay-20261018`。本報告依已完成的外部原始收據重算，沒有另執行產品或 profiler。

## 身分、建置與範圍

- 提案基底 `8ab0bdb467ba6e6d22f7c5652f221cffab4934b6` 與新 cherry-B 基底 `458e1de5b25f5ea8b0ef807bf1ce0c7fd8faf511` 的 Git tree 均為 `5669cb77eb0825d6c97f2e9bda3abc97075d6c54`；整棵 tracked tree 一致，提交歷史不同。
- support `ae868138bcc78d1718d9a58b0cab3944f0c4203e` 增加窄域 helper／測試，caller 仍原行為。enabled `68eed6fb…` 只切換 web bridge default 呼叫。withdraw `44da901dcee604b37b512c3d66c2a90caac055b4` 的整 tree 又與 support 相同。
- 相對基底只有 `geometry-core/transactions.inc`、`geometry-web/web_bridge.c` 與原 candidate product 的 C／Python harness 四檔變更。沒有改 SSOT、model-base caller 或原有測試斷言。
- 新路徑只對固定九行 default 程式、順序與前綴 World 前提成立時重用外層 owner：七行省內層候選，spec／guide 仍原候選。每行 revision、最終來源驗證、operation、OOM fallback、preview／history 政策由原 guard 與新增定向測試保護；不是所有 active transaction 都走捷徑。
- 正式比較固定 main `e980cb0dbf39beb40f6f3002a9ffbc43ee38c425`。後來的 main `a63e1999b5ebdc29ee30f25db6b319d6469bdac3` 只有 `決策佇列.md` 增 36 行，產品／建置輸入相同；**實測是 e980，未執行 a63**。
- 本輪有 8 份 binary manifest：main／integration × normal／gprof × bridge／model-base；皆 C11／`-O2`。gprof 模式帶 `-pg -g -fno-omit-frame-pointer`，manifest 記錄 main 2／integration 56 個 `.c` 依賴均有插樁。原始 `gmon.out` 是 profiling 資料；執行檔只列 SHA／重建命令，不作公共可執行附件。
- prepare 0.688 s、build 190.691 s、measure 6.528 s、profile 8.791 s，均 exit 0。建置與測試耗時不是性能倍率。

## normal 固定指令結果

每欄為本輪中位數。cold／model 各 7 次，resident 九階段各 15 次；各版本 resident 另有未納入樣本的啟動 dump 與節流探測。normal 和 gprof 各 **305 個 timing samples／23 組統計**，逐 raw JSON 核對 **288 個成功 bridge 回應及 21 個成功 model 輸出**。已從 samples 重算 median／p95／sum／同輪倍率，沒有 skip 或錯誤回應計入。

| workload / phase | 次數 | main ms | integration ms | 同輪倍率 |
|---|---:|---:|---:|---:|
| bridge-cold / cold_start_dump | 7 | 54.108 | 96.630 | 1.786× |
| bridge-resident / reset | 15 | 0.655 | 9.042 | 13.805× |
| bridge-resident / load_scene | 15 | 27.506 | 51.006 | 1.854× |
| bridge-resident / read_dump | 15 | 1.861 | 0.516 | 0.277× |
| bridge-resident / canvas_position | 15 | 2.963 | 7.223 | 2.438× |
| bridge-resident / unused_spec_create | 15 | 4.779 | 10.046 | 2.102× |
| bridge-resident / unused_spec_replace | 15 | 3.515 | 9.863 | 2.806× |
| bridge-resident / preview_spec | 15 | 3.609 | 7.116 | 1.972× |
| bridge-resident / cancel_preview | 15 | 0.403 | 2.750 | 6.825× |
| bridge-resident / read_final_dump | 15 | 0.508 | 0.583 | 1.147× |
| model-legacy / process_total | 7 | 53.612 | 177.892 | 3.318× |
| model-neutral / process_total | 7 | 未量測 | 162.442 | 無比較 |

完整 p95、min/max 與樣本見 `normal-comparison.csv` 及原 run 的 `samples.json`／`summary.json`。冷啟動涵蓋程序啟動、default 初始化與首個 dump；常駐逐指令時間排除其啟動階段。直接 C model-base 程序時間不包含 Python decoder／runtime。

neutral 中位數比 legacy 少 **15.450 ms**，不是來源圖負成本：兩組各七個獨立程序樣本，legacy 162.572–186.957 ms，neutral 161.386–209.040 ms，沒有 main neutral 對照。不得把兩中位數差當成純來源圖成本，或把跨輪 model 波動歸因於這次 default 改動。reset 與若干編輯階段仍明顯高於 main，未全面達到兩倍內。

## 正式 bridge suite 對照

兩版執行相同 `python3 -B -u tests/run_all.py --build --only py:test_bridge_integrity`，各自 checkout／正式 registry build；原 assertions 沒有變更。`tests/test_bridge_integrity.py`、`tests/_bridge.py`、`tests/run_tests.py` 的 Git blobs 兩版相同。

| 版本 | source | passed／run | skip | unittest s | JSON wrapper s | run_all process 含 build s |
|---|---|---:|---:|---:|---:|---:|
| main | e980cb0d | 24/24 | 0 | 38.161 | 38.230 | 53.305 |
| candidate | 68eed6fb | 24/24 | 0 | 81.171 | 81.310 | 112.611 |

採同層 unittest footer 計算：81.171 / 38.161＝**2.127066900763×**，未達兩倍內。沒有挑換 main 樣本或把含 build 時間混入倍率。原 JSON／unittest log／process 收據與精確雜湊見 `bridge-registry-verification.json`。

此 suite 的每次 `_bridge.run_once` 經 `find_bridge → _explicit → binaries.inspect_one` 檢查來源 fingerprint／binary 身分，並非直接呼叫 `require_fresh`。main／candidate sidecar sourcefiles 數量為 52／192；這只是來源集合大小，不是時間證據。目前原收據沒有逐方法、來源掃描或 child bridge 的分段計時，不能將剩餘倍率歸因於掃描、World 複製或 memcmp。後續若需定位，應對這個真 suite 另作診斷 profile，保持同樣 freshness／stderr／拒絕判決；不得拿診斷 profile 時間取代以上 normal 結果。

## gprof 觀察與限制

七組 profile 共 **37 個原始 gmon.out**；前 20 self／inclusive／calls 及完整 callgraph 已由原 helper 產生。main cold／resident／legacy 和 integration neutral 均 `no time accumulated`；integration cold 僅 0.01 s（geo_placement_definition_decode）、resident 0.04 s（四個符號各 0.01 s）、legacy 0.01 s（main）。樣本太少，不能用百分比排名指認剩餘效能主因；零 self 不等於零成本。

固定 workload 的原 gprof 符號計數對照 8ab → 68eed：

| integration workload | app_world_candidate_create | bind_core | geo_sha256 | geo_sha_block |
|---|---:|---:|---:|---:|
| cold（7 processes） | 70→21 | 630→189 | 357→112 | 3794→1617 |
| resident（含啟動 default） | 145→138 | 1305→1242 | 711→676 | 8177→7866 |
| model legacy | 70→70 | 630→630 | 350→350 | 3731→3731 |
| model neutral | 70→70 | 630→630 | 371→371 | 3857→3857 |

這與每次 default 省七個 inner candidates 的定向成本斷言一致；resident workload 的 reset 是空 World reset，故只在程序啟動 default 省七個。四組 `geo_eval_source` 原符號計數仍為 15225／60810／15225／16520；不是透過減少此指令串的來源求值計數獲取變化。

gprof 的 O2 inline／最近符號歸屬仍使 provider 出現源碼不存在的遞迴形狀；所有原符號表照存，但不能當成精確 source-level 次數或 metadata 成本。inclusive 是呼叫圖估算，不能相加或用其比例精分 H／K／provider。libc 未插樁，無法由這些表排除 memcpy／memcmp；profile elapsed 不作 normal 退化倍率。沒有實測硬體 cycles。

## 修前、修後、撤回與恢復

| 階段 | source | unittest 真結果 | unittest s |
|---|---|---|---:|
| support 修前 | ae868138 | 5 方法：4 pass、1 named cost fail | 6.993 |
| enabled | 68eed6fb | 26/26、0 skip | 17.972 |
| 只撤 caller | 44da901d | 同一成本方法真 fail | 6.613 |
| 只撤逐行 revision | 4f22ef5d | 指定方法真 fail | 7.202 |
| 只撤固定程式 literal 比對 | 8fe72e35 | 指定方法真 fail | 6.723 |
| 恢復 enabled | 68eed6fb | 8 modules，159/159、0 skip | 43.744 |

原生首個失敗訊息分別是 `ASSERT:default-owned-inner-candidate-cost`（修前與撤 caller 相同）、`ASSERT:default-spec-guide-keep-original-revisions`、`ASSERT:default-changed-program-rejected`。不是編譯／import／timeout 失敗。修前命令含五方法，撤 caller 命令只跑其中同一成本方法，不聲稱兩份完整 argv 相同。

enabled 真輸出包含 `inner=2 completed=50 restored=41 generation=1`，optional scratch OOM 為原 `inner=9`。恢復後八 modules 計數為 18＋17＋17＋7＋26＋53＋11＋10＝159。原始 stdout／stderr、argv、source 前後穩定性與分開的 process／unittest 耗時見 `fixes/perf-default-replay/readonly-review/evidence-ledger-v2.json`。

四狀態 support／enabled／withdrawn／restored 各六個真 bridge case、80 個固定命令。**54/54 組 stdin／stdout／stderr 比較逐 byte 相同**，包含冷啟動、default／reset、非零 revision、pending preview、undo／redo 與 history group；保留預期拒絕原文，沒有路徑、token、revision、空白或 CRLF 正規化。driver SHA `7cfbcbd4d0bd0440be5c03075e08b4ac087b208815ce81d682f3b703b3cccc07`，固定 fixture SHA `e1012d2b5fb10ed8cc37e22a1e193011792c023fd43f427a17982ba9e8425601`。這些 O0 NativeBuild bridge 是語意證據，不是正式性能樣本。

## 環境與未驗項

Debian GNU/Linux 13（trixie），Linux 6.18.55 x86_64、GCC 14.2.0、Python 3.12.14、GNU gprof 2.44，stack 16 MiB。本次 run 記錄五個可見 CPU。既有同環境版本收據為 Node v24.19.0、Google Chrome 155.0.8059.84；本性能階段沒有執行 Node／Chrome。

正式 bridge registry 的 ≤2× 門檻仍未達；完整非瀏覽器 strict census／整合瀏覽器重驗、model_update 原 timeout 內完成及 roots／其他未合修正仍須各自收據。本題不改 model-base owner 或合併來源圖，不將局部性能改善等同整體驗收完成。

## 公開範圍與提交邊界

本分支基於已含 A/D 的 integration `e9c1509cf89e6f35d298743ec5e3368370316cf7`，先依賴四個 B cherry-pick（`8f35eb41`、`cba159ca`、`49b1f2f3`、`458e1de5`），其最後 tree 與原 B `8ab0bdb4` 完全相同。本題自己的 source commits 只有 support `ae868138` 及 enable `68eed6fb`；兩份 patch 與三份單點撤回 patch 放在 `patches/`，未把 B 歷史重算為本題新修正。報告 commit／push 狀態不由本 inventory 宣稱。

公開集合由 `inventory.json` 精確列出，含所有本題已完成 recorder stages、四態 raw、正式 normal／gprof 原件、37 份 gmon 與真 registry 結果；依共用 collector 規則不公開任何 before/after.source.json 或 recorder.py。正式 registry 的四份大型來源快照仍留在外部原路徑，只列 receipt 已記 bytes／SHA；沒有改名繞過。公開資料無法重算未公開完整來源清單，`source_stable` 是原 recorder 觀測。公開性能 archive 的兩份小型 `source-manifest.json` 是原建置輸入索引，不是上述大型逐檔環境快照。

`gmon.out.raw`、`.link-map.txt` 與 fixture `.scene.raw` 是原 bytes 的資料副本，原路徑與雜湊映射見 `publication-data-mapping.json`；沒有修改 gmon 內容。可將 gmon 資料還原原檔名供 gprof 使用，仍須與對應 manifest 的 binary／符號相符。實際 binary、object、Python工具原碼與完整 archive sources 不發布，保留 manifest／原命令與工具 SHA；因此公開 payload 本身不是完整可執行工具包。

## 公開原件導覽

- [normal 全部樣本](performance/artifacts-adbd-68eed6fb/runs/20261018T224919274335-normal/samples.json)、[normal 摘要](performance/artifacts-adbd-68eed6fb/runs/20261018T224919274335-normal/summary.json)、[同輪比較表](normal-comparison.csv)。
- [本輪 gprof 原件](performance/artifacts-adbd-68eed6fb/runs/20261018T224925766853-gprof)、[獨立 profile 複核](profile-readonly-review.md)、[資料原路徑映射](publication-data-mapping.json)。
- [main 正式 registry 原 log](performance-main-registry/suite-logs/py_test_bridge_integrity.unittest.log)、[candidate 原 log](performance-candidate-registry/suite-logs/py_test_bridge_integrity.unittest.log)、[比值核對](bridge-registry-verification.json)。
- [四態 raw 比較](fixes/perf-default-replay/raw-comparison.json)、[功能台帳](fixes/perf-default-replay/readonly-review/evidence-ledger-v2.json)、[support 修前 stderr](functional-before-cost/command.stderr)、[撤 caller stderr](functional-withdraw-caller/command.stderr)、[恢復回歸 stderr](functional-restored-regressions/command.stderr)。
- [先前 B（8ab）已發布 profile 原件](https://github.com/ZhiQiYang/geometry-axiom/tree/a7d8a94fe1d95fb595812f1fe06f8b13a3222aea/evidence/geo261-codex-fix-perf-owned-replay-20261018/performance/artifacts-adb-8ab0bdb4/runs/20261018T215825197230-gprof)。

獨立 profile 複核原件保留其外部工作區相對路徑字串，未修改原件：其中 `../artifacts-adbd-68eed6fb/` 對應以上本輪 gprof 連結，`../artifacts-adb-8ab0bdb4/` 對應以上 B 永久連結，`../../fixes/` 對應本公開根的 `fixes/`。請以本節可點連結與 inventory 的目的地為公開導覽。publication-v1 原凍結版保留外部；v2 僅補本節導覽，所有原性能／功能／突變資料 bytes 不變。
