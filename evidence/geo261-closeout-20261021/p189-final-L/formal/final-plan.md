# 最終 L 的 P-189 確定執行計畫

這是新的確定來源版本，舊 `p189-L-plan.md` 與 L1 準備原件保持不動。現況只有純準備：三方 git archive 已新建並逐檔對 archive bytes 核對；沒有執行產生器自測、判定器控制、build、equivalence、timing 或 check。

分支：`codex/geo261-closeout-20261021`。

- main：`adbaebf9c73ea6801d7b4d5214e4b846b132923b`
- base：`3e600772076465fc65a26ac09055028301c0fb0b`
- final：`43f85313c32410ac01406ab585846bbacafea278`

來源目錄：`/workspace/geo261-p189-final-L-src.dqc1bplz`；輸出目錄：`/workspace/geo261-evidence/p189-final-L-43f85313c324-ready.g0dzrc03`。三方來源是 git archive，沒有 .git。固定 runner：`/workspace/geometry-axiom/geometry-core/domain-decoupling/closeout-tools/p189_verify.py`，SHA256 `fb42a801ce350e64444fcb2db433e59f8c2228546b4b594298581bdb365d0c44`；工具 bytes 與 L git blob 相同。固定產生器：`/workspace/geo261-p189-final-L-src.dqc1bplz/gen_scene.py`，SHA256 `347142beb7aa06c39969cd5bce35bacddc0734046eb7853e84d96f1ff9ef7c91`，原件來自交接 59796b1af9259eb23d30134c2ce5a56317a06091。

每個階段均分開保存 argv、cwd、工具 hash、開始／結束時間、原 stdout/stderr 及 actual wait code。執行前移除 PYTHONOPTIMIZE，避免 assert 控制被停用。以下指令只記錄，尚未執行：

```sh
python3 -B /workspace/geo261-p189-final-L-src.dqc1bplz/gen_scene.py --selftest
```

```sh
python3 -B -u /workspace/geometry-axiom/geometry-core/domain-decoupling/closeout-tools/p189_verify.py selftest --repo /workspace/geometry-axiom --work /workspace/geo261-p189-final-L-src.dqc1bplz --out /workspace/geo261-evidence/p189-final-L-43f85313c324-ready.g0dzrc03 --gen /workspace/geo261-p189-final-L-src.dqc1bplz/gen_scene.py --final 43f85313c32410ac01406ab585846bbacafea278 --timeout 900
```

```sh
python3 -B -u /workspace/geometry-axiom/geometry-core/domain-decoupling/closeout-tools/p189_verify.py build --repo /workspace/geometry-axiom --work /workspace/geo261-p189-final-L-src.dqc1bplz --out /workspace/geo261-evidence/p189-final-L-43f85313c324-ready.g0dzrc03 --gen /workspace/geo261-p189-final-L-src.dqc1bplz/gen_scene.py --final 43f85313c32410ac01406ab585846bbacafea278 --timeout 900
```

```sh
python3 -B -u /workspace/geometry-axiom/geometry-core/domain-decoupling/closeout-tools/p189_verify.py equivalence --repo /workspace/geometry-axiom --work /workspace/geo261-p189-final-L-src.dqc1bplz --out /workspace/geo261-evidence/p189-final-L-43f85313c324-ready.g0dzrc03 --gen /workspace/geo261-p189-final-L-src.dqc1bplz/gen_scene.py --final 43f85313c32410ac01406ab585846bbacafea278 --timeout 900
```

```sh
python3 -B -u /workspace/geometry-axiom/geometry-core/domain-decoupling/closeout-tools/p189_verify.py timing --repo /workspace/geometry-axiom --work /workspace/geo261-p189-final-L-src.dqc1bplz --out /workspace/geo261-evidence/p189-final-L-43f85313c324-ready.g0dzrc03 --gen /workspace/geo261-p189-final-L-src.dqc1bplz/gen_scene.py --final 43f85313c32410ac01406ab585846bbacafea278 --timeout 900
```

```sh
python3 -B -u /workspace/geometry-axiom/geometry-core/domain-decoupling/closeout-tools/p189_verify.py check --repo /workspace/geometry-axiom --work /workspace/geo261-p189-final-L-src.dqc1bplz --out /workspace/geo261-evidence/p189-final-L-43f85313c324-ready.g0dzrc03 --gen /workspace/geo261-p189-final-L-src.dqc1bplz/gen_scene.py --final 43f85313c32410ac01406ab585846bbacafea278 --timeout 900
```

判定器 16 控制只在 `selftest`（或 `all`）phase 執行；本輪明確單獨執行 `selftest`，不使用 `all` 混淆排程。16 筆為時間／樣本 10、dump 4、來源收據 2，合計 2 正控制、14 負控制。另有正常 provenance 的內部斷言，未另算一筆。只有實際跑完並取得本輪 validator-selftest.json 才報控制通過；不引用歷史控制充數。產生器 --selftest 是另一項，與這16筆分開保存。

build 固定 gcc -std=c11 -O2，不因帳本預設 cc 調整而更動三方 P-189 方法。equivalence 預期 4 份 generated 加 171 份 base 根目錄場景；generated 必三方成功且完整 stdout 相同，舊場景沿 base/final 完整 stdout 相同的原判準，main 差異另記。equivalence 程序回 0 只表示收集完成，還須核對收據 pass、complete。

timing 前另做三支 binary SHA256 對 build-receipt 的核對及環境快照，程序清單含 STAT，殭屍不當活負載；若有本次服務 idle bridge，先以對應服務與 CPU tick 確認，不擅殺服務。等待主代理確認所有 heavy 與封包雜湊停止後，才獨占執行36筆：每N三輪，main/base/final、final/base/main、main/base/final。計時從 Popen 回傳後至 communicate 完成，不冒稱含完整 Popen 成本。收樣 phase 返回0不等於門檻綠；timing-receipt 可能 pass=false。最後 check 才同時驗 SHA鏈、場景完整等價、每N final/main中位數 ≤2，正式返回0或1。check不會重跑16控制。

各階段真失敗均立即保留並回報；如果timing收完但比值超過2，仍執行check取得正式紅燈碼，不調門檻，不稱可合。正式結果之前，不啟後續diagnostic。

若最終 L 仍紅，#288 局部診斷候選為 definition_sources.c:17 的 wd_read 固定1/4/8 byte讀取是否在GCC14 -O2實際內聯／展開；只改相同解碼計算的候選方案可與memo分開評估，但目前未證明有成本或收益。先檢查正式binary反組譯，再決定是否需要獨占取樣。contact_order、排序／去重、跨consumer memo與失效方案留給#323／#300，不納入這個候選。

以下是正式紅燈後才考慮的最小靜態診斷命令（尚未執行；輸出目錄須先另建，不能覆寫正式原件）：

```sh
nm -an /workspace/geo261-p189-final-L-src.dqc1bplz/43f85313/bridge > /workspace/geo261-evidence/p189-diagnostic-L-43f85313c324/final-symbols.log
objdump -drwC /workspace/geo261-p189-final-L-src.dqc1bplz/43f85313/bridge > /workspace/geo261-evidence/p189-diagnostic-L-43f85313c324/final-objdump.log
rg -n 'wd_read|wd_placement_read|wood_definition_sources_placement' /workspace/geo261-evidence/p189-diagnostic-L-43f85313c324/final-symbols.log /workspace/geo261-evidence/p189-diagnostic-L-43f85313c324/final-objdump.log
```

這能辨識仍有通用 byte loop、constprop 特化或內聯後展開的實際機器碼；符號不存在不能直接判定已優化，必須看 caller。它不能量占比，更不能保證改善2×門檻。若仍有迴圈且值得量，後續才對同一 L／main、固定 N64（必要時N48）做獨占取樣；本次只做 PATH 查找，未找到 perf；未嘗試安裝、調整權限或取樣。現有 gprof 可供後續獨占診斷，但不可把任何帶 -pg 的診斷耗時當正式 -O2 成績。任何局部解碼候選須維持端序、邊界拒絕、讀取位移、錯誤黏著狀態及可攜 C11 語意；P-177 五入口次數與所屬時機、來源圖／輸出都不能改。

目前新增突變自證不適用：只準備來源及命令，未改產品。最不確定仍是 L 的正式比值及 wd_read 在正式 -O2 binary 中的實際成本；兩者都尚未量測。

若反組譯仍無法判斷成本，而正式 L 確認超標，需另行放行的最小剖析命令如下；本輪沒有執行。diagnostic/source 必須另由同 L 建 archive（不是改正式來源／binary），s64.scene 使用本輪同 hash 的輸入。由於 PATH 沒有 perf，以下選已存在的 gprof，保持 -O2 並另存帶 -pg 的 binary；這會增加量測擾動，僅用來定位 self／caller 成本，不用來宣告修正達標。

```sh
# cwd: /workspace/geo261-evidence/p189-diagnostic-L-43f85313c324/source
gcc -std=c11 -O2 -g -pg -fno-omit-frame-pointer geometry-web/web_bridge.c -o /workspace/geo261-evidence/p189-diagnostic-L-43f85313c324/bridge-profile -lm
# cwd: /workspace/geo261-evidence/p189-diagnostic-L-43f85313c324
# load.in 內容須固定為 loadfile /workspace/geo261-p189-final-L-src.dqc1bplz/scenes/s64.scene 加換行。
bash -c 'ulimit -c 0; ulimit -S -s 16384 || exit 126; exec ./bridge-profile' < load.in > load.stdout 2> load.stderr
gprof -b -p -q bridge-profile gmon.out > gprof.log 2> gprof.stderr
```

每條命令分別留 actual exit、編譯器版本／flags、binary/input hash。若 -O2 已內聯 wd_read，gprof 未列獨立符號不等於零成本，須將 placement/member 解碼 caller 與反組譯合讀；只有該組成本明顯才考慮固定寬度解碼實驗。若占比低，即否證這個優先假設，回報而不盲改。必要時以相同診斷方法量 main 對應載入階段，但不能拿不同 flags 的百分比直接做跨版效能門檻。

校準補正：第一次 /workspace/geo261-evidence/p189-final-L-43f85313c324.wfwk1_ca 的 generator-selftest 真實 exit1，因準備漏帶 calib/f3-00.scene。已保留其全部原件，未開始其他phase／沒有性能樣本。本輪使用新out，從同handoff 59796b1af9259eb23d30134c2ce5a56317a06091 blob 541434203427d34f64e560b34adac9d7ffaa2ffe 取回校準原bytes，SHA256 35e24fb0a483ffd6fee8dd99f751edeb127418481aa717816af804cd218024b2，共 16255 bytes；未改gen、正式工具或判準。三方未建置來源逐檔重核，原archive均同hash、三支bridge都不存在。
