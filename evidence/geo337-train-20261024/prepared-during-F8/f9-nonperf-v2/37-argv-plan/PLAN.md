# F9 正式原入口接續計畫（只準備，未執行）

F8=`75a1e93811a52b69385cbdaf6a09d773ed9052ad`。全123正在F8跑；F9目前未存在／未綁。root須先等真終態、封存原120 execution.head與3retired，獨審後只採用帳本JSON並普通push固定F9；清除所有MUTATE_*後原tracked check需真0。F8→F9除evidence外只能變tests/mutants_results.json，保存完整path/byte closure。若另變產品/tests/裁判，先重新判影響，不能套此清單。

R8已在F8有效完成：36樣本／4profiles；原性能全部綠，exact三差與compare1/outer1保紅。F9不能回填其execution SHA、不能重抽有效R8。F8帳本產生與F9採用/正式gate為不同身份。最新已讀#338審查是handoff7a31dc436c78f16979b8f4cb97550118355f6d3a中的2026-10-24T06:38:46Z/head597bce6：完整正式gate、原exact/perf、requiredCI仍須逐欄交代；本計畫不解除CI或exact。

## 先啟動 native 與 canvas 的準備

1. ROOT原路徑已在F8。全帳本停止後由root以保全方式普通detach到F9，保五fixtures、refs、sparse、全部原件及獨立可寫inode；不得reset/clean。新帳本採用不回寫F8 seed或原帳本raw。
2. Native原driver `763a6e8064be212a020522a43a80bdb6cd353d329997c83479f469c2359f4d21` 直接收 --sha F9，不重寫。COMMANDS.json含完整argv。它跑原 `ulimit -s 16384; python3 tests/run_all.py --build`，無selector；原strict registry、WindowsGDI唯一原Linuxskip不變。35min CI門檻仍有效，3倍watchdog只用收件，超35min不能稱CI通過。/tmp/geometry-tests是硬寫共享路徑，換TMPDIR不能隔離；native與required-eight不可並寫。先按原driver保留整個舊cache，不能刪原件。
3. Browser需完整source seed，不可直接採只有2738葉、排除docs/prototypes的full123最小seed。沿已審v3 preparer新私有pool、六job獨立gitdir/HEAD/index、各自TMP/profile/埠；nativeROOT與pool來源inode分離。舊L seed已immutable、禁止原地改。只重綁F9/SHA8/pool/out，原driver2a42523f與workflow不改；舊 `/workspace/launch_geo337_L_browser.py` 硬釘L，不能直接跑。機械rebind還須另一peer核。
4. 原preparer入口：`python3 -B /tmp/browser_readonly_pool_preparer_v3_seed.py --git-dir <OWNER_GIT> --sha <F9> --out <NEW_POOL> --reuse-seed <FULL_F9_SEED> --native-root /tmp/train337-323-f64d638f-source --seed-freeze-authorized --materialize-authorized --reserve-bytes <ROOT_ACCEPTED_RESERVE>`。前後 --guard，不能在canvas測量中掃pool。
5. canvas先排獨占、不能與native/編譯/其他Chrome並跑；其餘重工作最多兩個。六HTTP/CDP配置與完整Node argv在COMMANDS。每job依原workflow npm build、必備fonts、start_local/probe、原cases、原artifact順序。Chrome/Node/fonts真version輸出保存，Chrome缺即本環境無法執行，不可skip通過。canvas不加only、不改golden；其餘matrixflag只是原job scope。原CI分鐘為canvas35/assembly15/documents10/grid15/space15/timber20，不放寬。

## 專項原入口與不能混用的來源

- Q38／§7兩項／required-eight／PF3：新的可執行外稿 `/tmp/geo337-F9-nonperf-original-tools-v2-20261025/` 已備、待peer，保五原argv。原舊prep帳本/裁判pin已過期，8項676不能沿用；當前source_index18/load_residual14共681（其餘18/5/4/24/432/166不變），Q38原完整44（SPM01–44，含原等價分類不改）。新外稿metadata-only新/舊/恢復0/1/0，不是正式gate結果。§7 source會暫改後finally還原，必用獨立可寫checkout。
- P52：原run_special generic --sha可重用（工具pin先核）；短/tmp OUT、9私有埠/profile、main/fix/fix/main每批8，兩側各16、median fix≤main；五控制0/0/1/1/1、5000ms／900ms等全不變。獨占，不能同時native/full123。
- P189：原main adbaebf9c73ea6801d7b4d5214e4b846b132923b／base3e600772076465fc65a26ac09055028301c0fb0b／F9，不換成#323 b74。N16/32/48/64每版3交錯=36，逐點fix/main≤2，完整loadfile+dump逐bytes相同；原600/900/1800秒。若原full先因dumpassert紅且timing尚未開始，獨立timing-only只能從該輪原三ELF與原timingtail繼續、保full紅、不得重抽已有效樣本。
- Memo：原 `/tmp/geo323-train337-lineage-20261024/memo-proof-tools/run.py` 明確要求formal.source_sha==--sha。R8 formal是F8，禁止把--sha設F9來繞；還未跑的memo應另審原兩C錨點漂移，再用獨立真F8來源、原F8 formal receipt跑withdrawn/restored/ABC，明列actualF8與F9僅帳本closure。原whole-file退回可能連provider-hint/local-init/其他優化一起拿掉，不能直接跑舊整檔withdrawal。不改原斷言/數值，待memo專責補最小adapter/peer。這不允許自行解除exact政策。
- Reader三條：原sync生成、--check、tests/test_axiom_reader.py，原run_stage直接參數綁F9。生成後Git必仍clean。三stage各新OUT，原unittest51屬歷史數，當前以原registry真輸出為準。
- RC：原run_original_rc_method固定 `ReadingAOracle.test_rc_face_is_measured_along_its_unlined_run`；builder/checker各baseline/withdrawn/restored必0/1/0，只以原RC_PROOF_REQUEST_TEMPLATE精確一處替換生成外部variant。原五輸入pin、原方法與AssertionError/error/skip分類全保，不import另一套較弱測試。
- 閱讀A：保native-7（名稱歷史，不預宣告當前測數）、oracle-13、golden-source-proof、golden-generate/compare、mutants-only、完整quick；原driver對應命令均列。測完整矩形逐毫米與凹579由原quick方法決定，不用子集代替。獨立來源須沿22imports的R2修補物化，不能重用漏fixture的R1；舊兩stage launcher硬釘L須機械rebind，直接使用generic run_stage可避免舊L宣稱。golden proof所需evidence工具亦須精確物化，不是整個歷史payload。
- ReadingA cli-build/order是原診斷；保持原#335未核可CLI初放能力另案，只保observed-order與construction-route實際結果，不新增公理或改原接受規則。
- #314：fullnative須真正包含六原suite strict rows（stagger_commit/commit_paths/ordered_facts/wood_grid_application/native_grid_product/grid_inspector_contract）；Node inspector另真跑，原bridge、900秒與transcript都保留。M121已在full123原F8列，直接精確索引該原兩method/0-1-0/完整build與restored，無新產品問題不再另跑targeted M121，不把F8改標F9。
- 架構三條：COMMANDS末段generic stage可執行原architecture_contract.py、test_architecture_contract.py、test_product_architecture.py；F9真source/exit另保存。已採四檔真執行M6e50、F8採用，若onlyledger則604inputs無變，既有四檔/九反證保原M身份，不冒F9重產。

## 排程與收件

先fresh df，按每filesystem新seed/cache/完整raw/編譯峰值預算，永久Gitobjectstore、fixtures、receipts不碰。root唯一啟動且分派source lease；同ROOT/cardref/axiom/reader生成不可並發，shared /tmp/geometry-tests不可雙寫。全部真原argv、環境、SHA、原exit、完整stdout/stderr、reaper終態保全，red不放寬、不把缺步驟當通過，其他獨立gate照跑。對外current矩陣只一份，F8 R8/帳本execution、F9採用/新gate、E證據、D正文分列。

此目錄只讀工具與小metadata、產生計畫；未啟版本命令、build、Chrome、原judge或正式測試，未改任何分支。所有 `<...>` 保持未綁，不能原樣執行。正式root launch須先固定真F9、review/pins、OUT與資源預算。
