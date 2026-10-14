# #211 bridge apply-proj 堆疊診斷補充

基底 `3156cc1c9dc4d2abc9c833974769d3ec66a9d46e`，接續 `c82866a9fdb9b15d3fd724f307eb871eec7457e9` 的 CLI / model-base 報告。補齊 web_bridge 的直接 include 閉包，新增各檔核對 manifest；全部 Git blob SHA 符合固定來源。產品零改動。

一般 build：`gcc -O2 -std=c11 -g -fstack-usage geometry-web/web_bridge.c -lm -o /tmp/geometry211-bridge`，exit 0。先設 stack 16 MiB；8 MiB 僅屬明示的缺陷對照。測試透過 subprocess preexec 設 RLIMIT_STACK，input 為 `loadfile <scene>\ndump\n`。這是 bridge 場景載入路徑，不冒稱已完成 canvas 或逐條 UI 點擊。

| 場景 | 8 MiB exit | 16 MiB exit |
|---|---:|---:|
| _ax_r13_anchor_follows.scene | -11，stdout/stderr 皆空 | 0，loadfile 與 dump 均 ok:true |
| _ax_r10_hole_follows_piece.scene | 0 | 0 |
| _ax_r17_wall_column_face.scene | 0 | 0 |

後兩案兩種 stack 均載入成功且 stdout 全文相同；第一案的空輸出不能當作領域拒絕。每次命令、monotonic 耗時、exit 與未截斷 stdout/stderr 見 receipt.json 及各案檔。並非完整 native 測試。

另建 -finstrument-functions 診斷版（其餘旗標、constructor 追蹤與前報告相同），32 MiB 下跑第一案，exit 0。相對起始 frame 高峰 8,800,640 bytes、12 層邏輯函式：main → cmd_loadfile → parse_scene_file → apply_scene_line → apply_scene_line_candidate → apply_scene_line_unchecked → apply_applyproj_line → proj_apply_one → proj_rebind_aux → reference_fragment_candidate → guide_line_get_local_segments → poly_clip_line。具名位址、addr2line、原/插樁 .su、header 與 binary SHA-256 皆保留。此链無重複函式；不是已證實的遞迴爆堆疊。插樁含內聯進出並改變 layout，所以此數字只屬診斷版，不冒充原 binary 精確峰值。

本輪只補 bridge 動態證據，尚未執行完整 tests/run_all.py 的 8/16 MiB 對照，未搬移 World 配置、未做修復突變、未開修正 PR。不能宣稱 #211 已修復或正式 WSL 收據。
