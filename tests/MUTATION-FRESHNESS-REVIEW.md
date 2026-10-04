# #85 mutation inventory 與 freshness

本次起始 main `d620b36e5048c3bca098df87845f14a33e7639ca`，隔離分支
`fix/mutation-freshness-85`。#84/PR93 的 reviewed 與 merged tree 相同，post-merge
27 freshness tests 通過，#84 依明示指示回填並關單。#85 是獨立修復，未改公理或產品。

開工核對 issue85 open、無 assignee／接手留言；遠端所有分支無另一 mutation owner。
open PR95 是 reader，PR96 是 saved-model navigation，未競寫其產品檔案。
CLI GitHub API 被環境拒絕讀取；改用已連接 GitHub 的 search_prs 成功核對 open PR。

## 逐筆處置原則

原始 `mutate.py --check`：48 records，44 stale／1 invalid／3 retired，exit1。
44 stale 的逐筆原因都是被變異檔及 include 閉包已變；oracle 未變，不借用舊判決。
main source SHA256 `5a0d8f90f1`（前綴），舊紀錄 `7a00d35154`；references.inc
現版 `064fefb87b`，舊紀錄 `458f636b4e`。每項精確現版雜湊寫在 results。

M56 原 anchor `grid_line_coord_in` 已不存在，但同一 I23(b) 判定仍存在：
current_geometry.c 的 `world_validate_derived` 改用 `grid_anchor_line_coord`，並有
has_band/band 參數。恢復這個 anchor；沒有移除有效 mutant 或增加 retired。
三個既有 retired（M35、M51、M55）仍保留原移除依據，且舊 anchor 沒有復活。

## M01 反例與四項 equivalence 重新核對

獨立 reviewer 指出原 M01 proof 錯誤：I2／現行 poly_loop_is_valid 容許相鄰共線邊，
不是每個頂點都有水平邊接住。六頂點 loop (0,0),(100,0),(100,50),(100,100),
(0,100),(0,50) 在 baseline 與 M01 都合法；p=(100,50) 的 edge/point 判定，及
[80,20,100,50] 的 poly/boundary/surface 矩形包含，baseline 全 true、M01 全 false。
TEMP include harness 已實跑。撤回 M01 equivalent，由完整 oracle 給實際判決。

公開 `_ax_i5_collinear_vertex_rect_corner.scene` 在既有 L 形凹角輪廓兩側加入直邊
共線頂點；baseline 接受 4000 mm 角材，M01 拒絕。它納入 run_tests（139 scenes）
及 bridge 的接受型往返；test_core_integrity 增加八項合法性／包含／越界檢查（80→88）。
未改產品來排除反例，未減少任何既有 floor。

- M09／I5：hole bbox 恰相切時，孔點全部在矩形開內部的一側，三道細查（孔頂點
  嚴格在內、孔邊穿開內部、孔含四角）均為 false；快退改為細查不改結果。
  共線分段不改 bbox 或這些幾何半平面關係。
- M23／R6(d)：collect_stop_faces 枚舉 outer/hole 邊及同面已放 timber 側面。
  合法輪廓的共線相鄰邊只在端點相接，不能同時涵蓋正寬 [lo,hi]；反向回走
  會使後續非相鄰邊相交而被 poly_loop_is_valid 拒絕。非相鄰共線重疊亦被拒絕。
  孔不能相碰或貼輪廓；同線 timber 由 D11 dedup／stop_face_shadowed 保留先佔用
  支撐。因此此合法輸入 hits>1 proof 不依賴水平／垂直交替。
- M36／R6(e)：唯一呼叫鏈仍是 world_revalidate → reference_rebuild →
  reference_check_all → world_validate_derived。前一檢查已用相同 collect_stop_faces、
  footprint、ends、lo/hi、has_between 條件驗端面；之間只重建 spaces，不改支撐來源。
- M56／I23(b)：reference_place_geometry 先用 grid_anchor_line_coord 求相同
  grid/index/axis/has_band/band；重建失敗已返回。掛 boundary 時兩處傳同一 pointer；
  自帶 rect 時前處用合成 outline，後處用 NULL，placement_local_bounds 得同 bounds，
  subgrid 面積計算亦得相同 rect 面積（無 holes）。同一 guard 仍冗餘；不宣稱兩處
  boundary pointer 字面相同。spaces 重建不修改 grid/placement/anchor。

以上是現版呼叫鏈／幾何推理，不把有限測試當形式證明。四項亦實際跑完整現版 oracle；
若結果與 proof 衝突，記 invalid，絕不以 equivalent 掩蓋。

## freshness 與結果 receipt

沿用同一 mutate.py／run_tests.py。binary raw identity 及 atomic JSON write 共用
#84 的 binaries.py；source 仍按既有 CRLF→LF include 閉包語意，不混用 registry
較寬的來源集合。每次 baseline／mutant launch 前後核 source、oracle、cache 與 raw bytes。
結果保留現版 source/closure/mutant/oracle，另有 compiler command/hash/exit、執行 head、
raw binary hash、完整 baseline 及每次 mutant oracle 結果／exit／stdout/stderr hash。
結果 checksum 能抓誤改；不是能抵擋重新算 checksum 的安全簽章。

`--check` 只讀，不 compile／launch／改 results。檢查完整 assertion census、baseline
全過、判決與 attempts 一致、killed_by/crashed_on、proof 及 tool fingerprint。
clean checkout 沒有 TEMP executable 時檢查的是保存的執行證據，不冒稱檢查不存在的
現場 binary；同平台 cache 若存在，必須與已執行 hash 及 sidecar 相符，replacement 或
tamper 必 stale。不同平台 receipts 仍標明原執行平台，不能當 Windows GDI 驗證。

normal run_all 現在固定讀 versioned results 的 `mutation:check`，不接受外殼
MUTATE_RESULTS 偷換；CI 既有 run_all 入口因此也會拒絕 stale/invalid/blocked/survived。
這項是 exit-code-only inventory gate，48 mutant 不加到 assertion 數。既有 floors 保留。
重跑可用 MUTATE_CACHE 指定隔離 TEMP cache，沒有改 OS／SAC。

## 可重現非破壞負例

公開 tests/test_mutation_freshness.py：same-size/mtime binary tamper、不符舊結果的新
sidecar、source/result/command/proof 變更、missing/legacy receipts、baseline fail、
不完整 runner/timeout/shell failure、compile fail、真 retry identity 重驗及 source
run 途中改變。所有 byte fixtures 的 launch 都 mocked。既有 113 selftests 不降 floor。
對 frozen d620b36，改寫 legacy killed 的 why/killed_by 且沒有 execution receipt，
old check exit0；修復後 exit1。沒有执行 binary。

前次 7a00afb 的 39 killed／1 crashed／5 equivalent 與 138/138 場景結果已被
獨立審查的 M01 反例否定為完整判據；其舊 proof 與交付綠燈不能證明 M01 equivalent。
新增有效邊界回歸後，以工具／oracle 凍結的 head `1c501cc52d1e81f06ea28a9850cfda9e0f8de176`
重新取得所有 45 支的判決：exit0，40 killed／1 crashed／4 equivalent／3 原有 retired；
0 survived／invalid／stale／blocked，baseline 139/139。M01 的 killed_by 是新場景。
全部 raw binary hash 與 sidecar、receipt 一致；四項 equivalent 的完整 result／stdout hash
與 baseline 相同。其有限比較只支持前述幾何／呼叫鏈推理。

修復 candidate 在 d620b36 基底的完整 census：56 suites、1652 discovered／1651 pass／
0 fail／1 既定 GDI skip，exit0。只新增 py:test_mutation_freshness=24 與 mutation:check
exit-code-only，既有 floors 全部逐項相同。其後 main `28bac889f53c99f0aa029e01134d62547ab27c5c`
合併他人 PR95，reader floor 32→41；已整合，未競寫 reader，最終整合 head 的 ordinary
strict 結果與 exact head 在交付 PR 正文回填。既有 113 selftests 與新增 24 tests 均通過。

獨立修復首輪 full census 發現五項 reader 冪等失敗，未當作綠燈或更新 floor 的依據。
原因是新 M01 killer 改變衍生見證清單。按 AGENTS 的正典追溯同步契約重建唯一 HTML；
TEMP 差分驗證只增加三處 `<code>` 場景名稱（165 bytes），移除這三個 token 後與舊
HTML 完全相同，沒有版面／互動／補丁改動。sync rebuild／check 通過；reader=41
保留，後續 full gate 再驗冪等。main PR96 已合併為 `1c83b5e`，沿用它的 Node floor=294。

只讀 strict check 30 次 warm 中位數 137.845ms、p95 153.221ms；45 支 fresh mutant
沿用，compiler／oracle／sidecar writes=0，artifact bytes／mtime 不變。這是單機 warm
量測，沒有跨平台性能聲明。實際 M02 TEMP native 副本 same-size/mtime 改 byte：old
check exit0、fixed exit1；source/result 及重算 checksum 後仍矛盾的 receipt 亦 exit1。
control exit0，損壞副本從未執行。

本修復不聲稱新增公理、端到端產品功能、Windows SAC/GDI、實體 iOS 或 hosted CI green。

<!-- inventory:start -->
## 全部 48 項處置與 oracle

| ID | 開工問題 | 現版結果 | anchor file/count | 具體 oracle／理由 |
|---|---|---|---|---|
| M01 | stale source/closure | killed | current_geometry.c / 1 | _ax_i5_collinear_vertex_rect_corner.scene |
| M02 | stale source/closure | killed | current_geometry.c / 1 | _test_lshape.scene, _ax_i5_collinear_vertex_rect_corner.scene, _role_priority_ext_primary.scene, _role_ext_stop_primary.scene |
| M03 | stale source/closure | killed | current_geometry.c / 1 | _wit_d30_infinite_grid_binding.scene, _wit_d29_grid_system.scene, subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene |
| M04 | stale source/closure | killed | current_geometry.c / 1 | _wit_d30_infinite_grid_binding.scene, _wit_d29_grid_system.scene, subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene |
| M05 | stale source/closure | killed | current_geometry.c / 1 | subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene, room_a.scene, room_box.scene |
| M06 | stale source/closure | killed | current_geometry.c / 1 | subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene, room_a.scene, room_box.scene |
| M07 | stale source/closure | killed | current_geometry.c / 1 | _test_lshape.scene, _edge_concave.scene, _ax_i5_collinear_vertex_rect_corner.scene, _role_priority_mutant.scene, _role_priority_ext_custom.scene |
| M08 | stale source/closure | killed | current_geometry.c / 1 | _role_cover_short.scene |
| M09 | stale source/closure | equivalent | current_geometry.c / 1 | same output; proof above |
| M10 | stale source/closure | killed | current_geometry.c / 1 | _ax_i5_hole_vertex_touches_rect_edge.scene |
| M11 | stale source/closure | killed | current_geometry.c / 1 | _test_hole_auto.scene, _test_ambiguous.scene, _demo_ceiling.scene, _edge_upper_seg.scene, _mut_reval_free_hole.scene |
| M12 | stale source/closure | killed | current_geometry.c / 1 | subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene, room_a.scene, room_box.scene |
| M13 | stale source/closure | killed | current_geometry.c / 1 | subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene, room_a.scene, room_box.scene |
| M14 | stale source/closure | killed | current_geometry.c / 1 | _test_hole_auto.scene, _demo_ceiling.scene, _edge_hole_bottom.scene, _edge_rect_only.scene, _edge_rect_stops.scene |
| M15 | stale source/closure | killed | current_geometry.c / 1 | subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene, room_a.scene, room_box.scene |
| M16 | stale source/closure | killed | current_geometry.c / 1 | _edge_straddle_hi.scene |
| M17 | stale source/closure | killed | current_geometry.c / 1 | subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene, room_a.scene, room_box.scene |
| M18 | stale source/closure | killed | current_geometry.c / 1 | subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene, room_a.scene, room_box.scene |
| M19 | stale source/closure | killed | current_geometry.c / 1 | _mut_through_boundary.scene |
| M20 | stale source/closure | crashed | current_geometry.c / 1 | _test_lshape.scene |
| M21 | stale source/closure | killed | current_geometry.c / 1 | _edge_straddle.scene, _mut_notch_straddle.scene, _role_cover_short.scene, _edge_straddle_hi.scene |
| M22 | stale source/closure | killed | current_geometry.c / 1 | _test_free.scene, _edge_free.scene, _mut_free_hole_end.scene |
| M23 | stale source/closure | equivalent | current_geometry.c / 1 | same output; proof above |
| M24 | stale source/closure | killed | current_geometry.c / 1 | _edge_face_touch_only.scene |
| M25 | stale source/closure | killed | current_geometry.c / 1 | _test_ambiguous.scene |
| M26 | stale source/closure | killed | current_geometry.c / 1 | subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene, room_a.scene, room_box.scene |
| M27 | stale source/closure | killed | current_geometry.c / 1 | subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene, room_a.scene, room_box.scene |
| M28 | stale source/closure | killed | geometry-core/references.inc / 1 | _test_grid_panel.scene, _edge_grid_panel_from.scene, _role_ext_stop_primary.scene, _wit_i13_odd_width.scene |
| M29 | stale source/closure | killed | geometry-core/references.inc / 1 | _demo_ceiling.scene, _edge_hole_anchor.scene, _edge_hole_bottom.scene, _edge_rect_stops.scene, _edge_stop_ambiguous.scene |
| M30 | stale source/closure | killed | geometry-core/references.inc / 1 | _edge_hole_anchor.scene, _edge_hole_bottom.scene, _ax_i5_hole_vertex_touches_rect_edge.scene |
| M31 | stale source/closure | killed | current_geometry.c / 1 | _mut_grid_dup.scene |
| M32 | stale source/closure | killed | current_geometry.c / 1 | _edge_grid_at_border.scene |
| M57 | stale source/closure | killed | current_geometry.c / 1 | subgrid-local.scene, demo-two-timbers.scene, _edge_rect_stops.scene, _test_between.scene, _edge_between_blocked.scene |
| M58 | stale source/closure | killed | current_geometry.c / 1 | demo-two-timbers.scene, _edge_rect_stops.scene, _test_between.scene, _edge_between_blocked.scene, _role_between_priority.scene |
| M51 | retired | retired | current_geometry.c / 0 | existing removal proof |
| M52 | stale source/closure | killed | current_geometry.c / 1 | _test_grid_redeclare.scene, _edge_grid_locked.scene |
| M56 | invalid anchor | equivalent | current_geometry.c / 1 | same output; proof above |
| M53 | stale source/closure | killed | current_geometry.c / 1 | _test_grid_panel.scene, _edge_grid_panel_from.scene |
| M54 | stale source/closure | killed | current_geometry.c / 1 | _mut_grid_panel_edge.scene |
| M55 | retired | retired | current_geometry.c / 0 | existing removal proof |
| M33 | stale source/closure | killed | geometry-core/references.inc / 1 | subgrid-local.scene, _test_grid.scene, _test_lshape.scene, _test_hole_auto.scene, _test_ambiguous.scene |
| M34 | stale source/closure | killed | geometry-core/references.inc / 1 | subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene, room_a.scene, room_box.scene |
| M35 | retired | retired | current_geometry.c / 0 | existing removal proof |
| M36 | stale source/closure | equivalent | current_geometry.c / 1 | same output; proof above |
| M37 | stale source/closure | killed | current_geometry.c / 1 | subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene, room_a.scene, room_box.scene |
| M38 | stale source/closure | killed | current_geometry.c / 1 | _mut_neg_hole_ref.scene |
| M39 | stale source/closure | killed | current_geometry.c / 1 | subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene, room_a.scene, room_box.scene |
| M40 | stale source/closure | killed | current_geometry.c / 1 | subgrid-local.scene, ceiling-a.scene, demo-two-timbers.scene, room_a.scene, room_box.scene |
<!-- inventory:end -->
