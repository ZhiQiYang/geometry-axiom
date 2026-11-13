# GEO-261 最終整合驗收準備（尚未執行）

2026-10-16。這是現有入口的只讀核對與執行順序，不是通過收據。當前九階段 targeted run 不受本文件影響。正式來源 SHA 由 root 完成整合後提供；207 條作用域清冊的三項追加答覆、SSOT 採納 A/B 及唯一正典同步仍是獨立前置。

## 來源與隔離

- 所有 WSL 編譯、測試、Node、Chrome 均經既有 `wsl_locked3.sh` 共用鎖；不改鎖、不啟動第二個 heavy 執行器。
- 每個固定來源使用 Linux ext4 checkout、獨立 `/tmp`、loopback、TEMP feedback、16 MiB stack，PATH 加 `/opt/node/bin` 及私有 `python -> python3`。不接使用者服務。
- 每份收據保留 source/runner/judge/fixture/binary/sidecar 雜湊、工具版本、UTC、原始 log/exit、實際發現數、fail/error/skip、前後 tracked manifest。重試另開輸出目錄，不覆蓋紅燈。
- 最終來源的 `tests/run_all.py`、`tests/run_all.expected.json` 及 workflow 在執行前重新讀取；本文不固定舊測試總數、不使用 `--update-expected` 修紅燈。

## 1. 全量 mutation：必須在最終 SHA 之前完成帳本提交

以下命令在受鎖的固定來源 checkout 內、獨立 TEMP 環境執行；`OUT` 是新的 repo 外收據目錄：

```sh
ulimit -s 16384
python3 -u tests/mutate.py --selftest
MUTATE_RESULTS="$OUT/mutants_results.json" python3 -u tests/mutate.py
MUTATE_RESULTS="$OUT/mutants_results.json" python3 -u tests/mutate.py --check --killers
```

無 ID 參數的 `mutate.py` 才是全量。既有等價／retired 的理由及裁判保留；搬檔不構成刪除 mutant 的理由。blocked、timeout、無法啟動不算 killed；已定義的 crashed 與 killed 分開報。

**關鍵接線：`run_all.py` 的 mutation-check 路徑明確把 `MUTATE_RESULTS` 設為該 checkout 的 `tests/mutants_results.json`。** 僅在 repo 外重產不會使正式 native job 讀到新帳本。先把外部原始帳本及 log 交 root 審閱，以正常提交納入 `tests/mutants_results.json`，再凍結最終 SHA。帳本提交若不改 product/include/judge/fixture，原四組內容雜湊可維持新鮮；最終 SHA 仍須重新 `--check`。不能用外部 env 繞過 aggregate 的固定帳本。

尚需核對的實作 gate：新 C 抽離若引入巢狀 include，mutation 定位／展開及來源閉包必須支援新路徑；當前提案明列此事，不能假定既有 runner 自動支援。Python／架構 scanner guard-removal 證據須另保留，不能假稱原生 scene mutants 已測到 Python。

## 2. 完整非瀏覽器

最終固定 SHA、已提交的新帳本及新鮮 binary registry 下執行：

```sh
ulimit -s 16384
python3 -u tests/run_all.py --build
```

必須是沒有 `--only`／`--extra-py`／`--simulate-missing` 的完整 run。逐 suite 與來源內 expected 比對；只接受 runner 原有、具名且實際報出的平台 skip，不把 skip 算 pass。targeted receipts 不補足缺跑的 suite。

現有 P0 namespace/manifest/原始輸出做法可重用；當前 `run-native-*.py` 僅是指定 unittest 模組的收據，不能拿它們冒充完整 aggregate。七 job train 的 native job 本身也會執行此命令；可把該次完整 native 收據作最終 aggregate 證據，避免沒有原因的重複全跑。

## 3. 七個正式 workflow jobs

既有 shared runner 會從固定 SHA 自己的 `.github/workflows/integration-tests.yml` 讀 job、env、matrix 與 `run:` 步驟。可重用的入口（以下 `<FINAL_SHA>`／`<FRESH_OUT>` 待 root 凍結）為：

```text
wsl -d Ubuntu-24.04 -- env WSL_CI_REPO=/mnt/d/geometry-axiom WSL_CI_OUT=<FRESH_OUT> bash /mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_locked3.sh ci <FINAL_SHA> all
```

`<FRESH_OUT>` 選 `/mnt/d/geometry-axiom-work/geo261-evidence/p1/final-seven-jobs-<sha8>-v1` 等尚不存在路徑。執行前另凍結 `wsl_locked3.sh`、`wsl_ci.sh`、`ci_run.py`、`ci_job.py` 的指紋。不要把七項直接在同一個現用服務跑。

目前 workflow 的實際測試命令如下；最終 SHA 若有正式變動，以其真實 workflow 為準並記差異：

| job | 命令 |
|---|---|
| native | `ulimit -s 16384`，接 `python3 tests/run_all.py --build` |
| assembly | `GEOMETRY_CDP_PORT=9367 GEOMETRY_ASSEMBLY_ONLY=1 node geometry-web/cdp_test.js` |
| documents | `GEOMETRY_CDP_PORT=9366 node geometry-web/documents_browser_test.js` |
| grid | `GEOMETRY_CDP_PORT=9334 GEOMETRY_GRID_SYSTEM_ONLY=1 node geometry-web/cdp_test.js` |
| canvas | `node geometry-web/cdp_test.js` |
| space | `GEOMETRY_CDP_PORT=9347 node geometry-web/space_model_test.js` |
| timber | `GEOMETRY_CDP_PORT=9348 GEOMETRY_TIMBER_ONLY=1 node geometry-web/space_model_test.js` |

六個 browser jobs 都先 `npm run build`，要求 Chrome、Noto CJK，開專屬 `start_local.py --port 18839` 並通過 `runtime_version.py --probe 18839`；runner 會機械隔離 port/TEMP/checkout。canvas 的 WSL wait trace 準備及退出時 archive 也屬 workflow，不能略過。正式 full canvas golden 與 full space census 保留；partial grid/assembly/timber 不取代 full。原 runner 有已明訂的 timeout／native baseline-qualified rerun 分類，原始首跑 exit/count 一律保留，browser failure 不自行豁免。

## 4. 所有舊 fixture 的逐件 reopen／重建

可重用的盤點是 `D:/geometry-axiom-work/geo261-research/FIXTURE-MANIFEST.json` 和 `FIXTURE-COMPATIBILITY.md`。其基準是舊 `1c807511`，不是最終來源：1246 scene、149 gcanvas、121 zip、52 schema-bearing JSON 僅是歷史盤點。需先對 `a898ad6e` 與最終 SHA 重新列 tracked 路徑／Git blob／raw SHA，保留每個容器 owner、producer 與原始 bytes；不得只枚舉 `tests/fixtures`。

目前尚未找到可直接重用的「全部家族 × baseline/candidate」完整 reopen runner。現有入口可覆蓋有明確 oracle 的部分：

- 原生 scenes／原子拒絕：完整 `tests/run_tests.py`（已在 aggregate）、`python3 tests/test_bridge_integrity.py`、`tests.test_reference_contract`、`tests.test_scene_import`。
- 模型舊包與保存結果：`tests.test_engineering_model_compatibility`、`tests.test_section_profile_modeling`、`tests.test_space_modeling`、`tests.test_model_update`、`tests.test_scenario_verify`，以及真正 frozen main producer 五包與 source-subdivision 拒絕。
- 直接模型包：`python3 geometry-core/modeling_cli.py verify <original-package.json> --base-executable <fresh-model-base>`；不能重新 build 同名包代替讀原包。
- 既有實際 chooser roundtrip：`GEOMETRY_SAVE_REOPEN_ONLY=1 node geometry-web/space_model_test.js`、`GEOMETRY_ENGINEERING_WORKFLOW_ONLY=1 node geometry-web/cdp_test.js`、grid workflow、`node tests/test_section_profile_browser.js`、`node tests/room_outline_acceptance_browser.js`、`node tests/test_grid_rule_reader_browser.js`。各自仍只證明其具名案例。
- `node tests/k2a_zip_browser.cjs` 要兩個不同的隔離服務與既有 receipt env；它的 OS writer 是明示 stub，不能稱為所有 archive chooser 驗證。

缺的交付是逐路徑結果表與通用差分接線：同一原始 bytes 分別經舊／新 executor，比 accept/reject、指定 code/clause、dump、typed refs、完整資產／草稿／owner、保存模型 source/geometry、拒絕原子性，並保留獨立既有幾何 oracle。229 組同 scene bytes 可共用 native 重放，但不能省掉容器 closure。歷史 failed/recovered evidence 先按同目錄 producer/receipt 分類，不能從檔名推定應接受或應拒絕。`unclassified`、`missing`、`skipped`、`blocked` 必須逐列保留，不能把七 job 綠燈改稱全部 fixture 綠燈。

## 5. Framing oracle

目前 main 及 integration checkout 沒有 `geometry-core/framing-template/oracle/`。既有提案指定 #251／#254 合流後原位保留、歸 W、核對內容摘要且不改內容，命令是：

```sh
cd geometry-core/framing-template/oracle
python3 selftest.py
```

必須先確認最終來源已包含完整 oracle 及其原始指紋。若仍未納入就報未納入，不能從另一分支複製半套或捏造成功。此 selftest 不替代生產端木工／核心負控。

## 6. 其餘不可由七 job 代替的 gate

- 已批准的最終 SSOT／作用域清冊、A/B modeling tuple、原歷史 tuple／能力年代守門、P1 adoption guard-removal 收據。
- 唯一正典的同步、`--check`、reader suite；前言及 §四完整可見、桌面／手機／無 JS／print／匯出批註的真瀏覽器檢查。不得新增第二份 reader。
- `python3 geometry-guide/witness.py --check --exe <fresh-core>` 的全部既有見證逐 bytes 核對，不先強制重建圖去消除差異。
- 完整 K/W/H 可執行來源 census、實際 dependency CLI 負向注入與 guard-removal、無 W 的純 K build/import、第二矩形模板；純新增 helper 綠燈不足以證明原產品已接線。
- 各新增 K 演算法在真產品 consumer 的 removal control、全部原場景／dump／來源契約維持。當前 rename Undo 紅燈要先分類修正並另留重跑收據。
- `tests/INTEGRATION-GATES.md` 與 `RELEASE-CANDIDATE.md` 已列但不在七 job 的 owner／browser 正式入口，須按本次受影響範圍逐項對照；不能把 `run_all` 的「列出入口」當作已執行。
- 最終整合審查與尚未消除的限制逐條交付；任何單一 gate 未執行都保持明列。
