GEO-246 的本機驗證收據；32 筆輸入及新舊釘點見 [32-pins.md](32-pins.md)。

`baseline.json`、`generic.json`、`restored.json` 記錄相同的實際輸入：原版 32 pass，四個訊息出口退回泛稱後 32 reason-failure，還原版 32 pass。`summary.json` 記錄四份來源逐位元組還原與來源雜湊。generic probe 的 exit 0 是稽核成功偵測 32 個真正的 unittest failure，不是產品通過。

probe 的可重跑入口是 `python3 tests/geo246_weak_pin_probe.py --bridge <fresh-bridge> --output <receipt.json>`；對故意退化的獨立 bridge 加上 `--expect-generic`。它使用原契約測試及 reject()，只將原因字串不符延至 cleanup 報紅，以便收齊 32 筆；其他失敗照常中止。

`mutants.log` 的合併訊息將 50 筆稱為 executed records；精確範圍是 47 筆實際編譯執行、3 筆原定義 retired 而未編譯。正式結果為 killed 42、crashed 1、equivalent 4、retired 3；stale／blocked／survived／invalid／unrun 均為 0。結果本體是 `tests/mutants_results.json`，freshness 使用原 `tests/mutate.py --check` 驗證。


- WSL Ubuntu 24.04、GCC 13.3、Python 3.12.3、Node 24.21.0；測試使用 `ulimit -s unlimited`，原生輸出與變異快取均位於本工單專用暫存目錄。私有 mount namespace 將專用目錄映射到 runner 固定的 `/tmp/geometry-tests`，未置換使用者服務或其他裁判的 binary。
- `python3 tests/binaries.py build`：WSL 所有可用原生目標（core、bridge、integrity、model-base、engjson）都在 C 修改後重建，指紋皆 fresh。Windows 用獨立 TEMP 跑原建置入口，6 個目標均編譯；core、bridge、integrity、gdi、engjson 為 fresh，model-base 重試 3 次仍被 SAC 擋（WinError 4551），未取得 fresh sidecar。未停用安全設定。
- 三個 grid 契約 suite：13 + 25 + 31 = **69/69 通過**，完整 runner 也再次跑過，fail=0、skip=0。
- `python3 tests/run_all.py --build`：**83/83 suite 已呼叫**，有計數項目共 2656，pass=2633、fail=22、skip=1；真實 exit=1。這一輪沒有使用 `--only`、`--allow-skip` 或改 expected 來放行。
- 整輪中的 Node 17 項失敗與 645／651 數量差異來自暫存 PATH 只有 `python3`、沒有部分既有 JS 測試需要的 `python` 命令（`spawn python ENOENT`）。補上**本工單暫存目錄內**指向 `/usr/bin/python3` 的別名後，以原 runner `python3 tests/run_all.py --build --only node:tests-js` 重跑整個 Node suite：**651/651 通過**、fail=0、skip=0、exit=0。這是局部重跑，未冒充第二輪完整驗收；原整輪失敗日誌保留為 `run-all.log` 與 `node-original.log.gz`。
- 本分支 `test_axiom_reader.py` 為 36 pass／5 fail；相同 WSL 環境對 PR #193 基底 `7b603b4dc34bbbf41731f0e7845d0519dd876c71` 獨立跑該檔，同為 36 pass／5 fail，失敗名稱全等。失敗均涉及既有 HTML 與重建結果的追溯範例差異（`_edge_grid_panel_shrink.scene` 與 `_ax_i5_notch_cell_corners_on_ring.scene`）。本工單禁止改閱讀器，因此保留原檔並明列未綠項，不宣稱完整驗收通過。
- WSL 的 GDI suite 因平台限制 skip；Windows 已單獨跑 `python tests/test_gdi_contract.py`，**1/1 通過**。其他 skip 的名稱及允許理由以完整 `run-all.log` 為準。
- `git diff --check` 通過；`current_geometry.c` 共 13099 個 CRLF，bare LF=0；禁止修改的五個路徑與基底無差異。

基底與本分支共同失敗的閱讀器測試：

- `test_color_contract_allows_unrelated_properties_and_untracked_selectors`
- `test_current_layout_change_does_not_relock_historical_migration_tests`
- `test_legacy_image_handler_retires_without_changing_live_svg_handler`
- `test_rebuild_is_byte_idempotent_and_keeps_reviews`
- `test_retired_color_migrations_allow_format_and_unrelated_layout_changes`

未驗／未完成：

- 完整 runner 收據為 exit 1，尚未全綠；Node 的環境錯誤已以 651/651 局部重跑消除，未重跑整輪。其餘閱讀器 5 項在基底已失敗，未修改本工單禁止修改的閱讀器。
- Windows model-base 啟動受 SAC 阻擋，Windows 建模契約未跑；相同 C adapter 的 WSL 建模契約已跑。
- `cdp_test.js`、`space_model_test.js`、正式 owner／真瀏覽器整合閘門未執行，這些不包含在 `run_all.py`；本次未改 JS 或 UI。完整 runner 列出的其他獨立整合入口也未驗。
- 正式 `【WSL 裁判】` 收據及 `【dot】` 審查待提供；維持 draft，未合併。

所有已跑命令的 exit、耗時與 stdout、三個契約 suite 的 JSON、基底閱讀器對照及環境／binary SHA-256 皆已存入 `tests/evidence/geo246-weak-pins/`。收據對應實作 commit `e73ebcb3ae8d72de06ceb4df692404dad83f7d33`；後續 commit 只加入收據及重新生成的變異結果，不更改已測產品或斷言。

較長的原始日誌使用標準 gzip 保存，解壓後逐位元組等於原輸出；`log-archives.json` 記錄原始 SHA-256 與長度。`run-all.log` 及命令／suite JSON 維持可直接讀取。
