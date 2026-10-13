# #211 雲端堆疊診斷（部分範圍，未修復）

來源 main `3156cc1c9dc4d2abc9c833974769d3ec66a9d46e`；領取提交 `7f23432472c7927f05292013b74a917a3af36c5c`。透過 GitHub 連接取得固定 SHA 的文字檔，source/scene manifest 的全部檔案經 Git blob SHA-1 核對相同。不是完整 git clone；沒有把此副本宣稱為完整 native 收據。

## 結果

- `python tests/run_tests.py /tmp/geometry211-core`：8 MiB 為 125 pass / 14 infrastructure / 0 assertion fail，exit 2，2.298882 秒；16 MiB 為 139 pass / 0 fail / 0 infrastructure，exit 0，2.530086 秒。14 個異常都是子程序 -11。全部原始 stdout/stderr 與 runner 結果 JSON 在 native*.stdout；不將 infrastructure 算成 assertion failure。
- 同支未插樁核心、subgrid-local.scene：9 MiB 三次 -11，9.5 MiB 三次 0；更小的 8–9 MiB 全部崩潰。完整逐次數據為 probe.json / limits.json。這是本環境可用堆疊上限的觀測區間，含初始 argv/environment、頁面與 ASLR，不是精確的函式堆疊位元組數。
- `StaggerModelCompatibility.test_adapter_rejects_literal_zero_multiples_missing_extra_and_outside_band` 的第 8 個 source：從原 scene() 的 AST 執行後附加原始 subgrid 行，見 model-source8.scene。直接 model-base 8 MiB exit -11、stdout/stderr 皆空；16 MiB exit 1，回 JSON `INVALID / BASE_INVALID / I9` 與 `I24：有相位差的主格不能建立子網格`。此處正常領域拒絕本來就是 exit 1；不是失敗。沒有在 Python modeling/base.py 層重跑 BASE_PROTOCOL 包裝。

## 堆疊定位

原 `-O2` 編譯器 `.su`：main 2,941,120 bytes；apply_subgrid_line 5,811,664 bytes，兩個同時存活的框架已達 8,752,784 bytes，超過 8 MiB。apply_subgrid_line 的 `World trial=*world` 與 `World backup=*world`（subgrid_commands.inc）形成主要配置；main 的 `World world` 也是大型區域配置。不能只把兩個框架的加總視為高峰。

另建獨立插樁二進位：`-finstrument-functions`、相同 O2，加 `trace211.h`，以 constructor 的 frame address 作起始基準；32 MiB 下實跑 subgrid-local.scene 得 `peak_relative_bytes=9542672`、15 層邏輯函式進入。完整具名鏈見 trace-symbols.txt：main → parse_scene_file → apply_scene_line → apply_scene_line_candidate → apply_scene_line_unchecked → apply_subgrid_line → world_revalidate → world_revalidate_candidate → world_validate_derived → grid_is_valid_in → grid_axis_lines_in → grid_cell_bounds → grid_axis_lines → placement_local_bounds → polygon_loop_bounds。

這條高峰鏈没有重複函式，不是已證實的遞迴堆疊溢位。GCC 插樁可能包含內聯函式的進出，也改變框架布局；trace-stack.su 的 main 2,905,920 bytes 與原 binary 不同。因此 9,542,672 只屬插樁版本的相對實測，不冒充未插樁版本的精確峰值或整個程式的全域最深鏈。原 binary 的限制對照獨立保留。

## 邊界

本次完成的是 CLI 139 場景與 model-base source8 的雲端診斷，不是 tests/run_all.py 的完整 86 suites，不是 WSL 七項，也沒有補 bridge apply-proj 的實際呼叫鏈。尚未修復、沒有突變修復證據，不建修正 PR、不改公理或產品、不降低 CI stack。下一輪須涵蓋完整 native 與 bridge 路徑，再驗證配置搬移不影響交易回滾、錯誤與重入；此報告不能作為已修復或可合併證據。
