# -*- coding: utf-8 -*-
"""current_geometry 測試執行器。

每個測試 = 一份 .scene + 預期:
  expect: "accept" | "reject"
  lengths: accept 時,依序比對輸出中所有「尺寸:L=…」的值
  error:   reject 時,本夾具的「路徑:[行號:]診斷」必須包含此子字串
  contains: accept 時,stdout 必須包含此子字串(可多條)
  not_contains: accept 時,stdout 不得包含此子字串(可多條)——
                用來驗「什麼都沒發生」這種主張,光靠 accept 驗不到

用法:
  python tests/run_tests.py [exe 路徑]      # 預設 ../cg_new.exe
"""
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

# Revised acceptance oracle: 2026-09-18 D7/I8a/I12/R2/R4.
TESTS = [
 {'scene': '_ax_r7_remote_flush_corner.scene', 'expect': 'reject', 'error': 'R7: 投影接觸非單一矩形'},
 {'scene': '_ax_r7_remote_flush_strip.scene', 'expect': 'reject', 'error': 'R7: 投影接觸非單一矩形'},
 {'scene': '_ax_r8_three_residual_components.scene', 'expect': 'reject', 'error': '拆分退化'},
 {'scene': '_ax_r8_three_residual_strip.scene', 'expect': 'reject', 'error': '拆分退化'},
 {'scene': '_ax_r7_rectangle_plus_line.scene', 'expect': 'reject', 'error': 'R7: 投影接觸非單一矩形'},
 {'scene': '_ax_r7_strip_plus_line.scene', 'expect': 'reject', 'error': 'R7: 投影接觸非單一矩形'},
 {'scene': '_ax_r7_rectangle_plus_point.scene', 'expect': 'reject', 'error': 'R7: 投影接觸非單一矩形'},
 {'scene': '_ax_r12_uncut_complex_strip.scene', 'expect': 'accept'},
 {'scene': '_ax_r15_uncut_strip_missing_item.scene', 'expect': 'reject', 'error': '不存在'},
 {'scene': '_ax_r14_uncut_strip_multiple_pieces.scene', 'expect': 'reject', 'error': '橫跨拆分線'},
 {'scene': '_ax_r7_notch_disconnected.scene', 'expect': 'reject', 'error': 'R7: 投影接觸非單一矩形'},
 {'scene': '_ax_r7_ridge_crossing.scene', 'expect': 'accept',
  'contains': ['(60, 70)', '(40, 80)'], 'not_contains': ['孔 #0']},
 {'scene': '_ax_r7_ridge_strip.scene', 'expect': 'accept',
  'contains': ['(60, 70)', '(40, 80)'], 'not_contains': ['孔 #0']},
 {'scene': '_ax_r7_point_tangent.scene', 'expect': 'reject', 'error': 'R7: 投影接觸非單一矩形'},
 {'scene': '_wit_d30_infinite_grid_binding.scene', 'expect': 'accept'},
 {'scene': '_wit_d29_grid_system.scene', 'expect': 'accept'},
 {'scene': '_wit_i37_grid_system_missing.scene', 'expect': 'reject', 'error': 'existing surface and grid-system'},
 {'scene': 'subgrid-local.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960, 2960, 1980]},
 {'scene': 'ceiling-a.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960]},
 {'scene': 'demo-two-timbers.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960, 2960, 1973]},
 {'scene': 'room_a.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960],
  # GEO-075:兩支同規格 → 加總 x2;不同規格分列。
  'contains': ['=== 下料清單 ===', '4000x20x20 boundary x2（角材 90、91）',
               '2960x27x33 primary x1（角材 1）', '合計 3 支，2 種規格，總長 10960 mm']},
 {'scene': 'room_box.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960]},
 {'scene': 'room_full.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960]},
 {'scene': '_test_fixed.scene', 'expect': 'accept', 'lengths': [4000]},
 {'scene': '_test_free.scene', 'expect': 'reject', 'error': '自由邊'},
 {'scene': '_test_hole.scene', 'expect': 'accept', 'contains': ['參考線 1（段 0）', '孔 #0']},
 {'scene': '_test_tx.scene', 'expect': 'reject', 'error': 'I8a'},
 {'scene': '_test_tx2.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960]},
 {'scene': '_test_grid.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960]},
 {'scene': '_test_lshape.scene', 'expect': 'reject', 'error': '沒有擋面'},
 {'scene': '_test_hole_auto.scene', 'expect': 'accept', 'lengths': [4000, 1180]},
 {'scene': '_test_ambiguous.scene', 'expect': 'reject', 'error': '跨距歧義'},
 {'scene': '_test_collide.scene', 'expect': 'reject', 'error': 'R6'},
 {'scene': '_demo_ceiling.scene', 'expect': 'accept', 'lengths': [4000, 2946, 4000, 2946, 2946, 2946, 1173]},
 {'scene': '_edge_axis_violation.scene', 'expect': 'reject', 'error': '垂直'},
 {'scene': '_edge_concave.scene', 'expect': 'accept', 'lengths': [4000]},
 {'scene': '_ax_i5_collinear_vertex_rect_corner.scene', 'expect': 'accept', 'lengths': [4000]},
 # GEO-257:凹槽(環外)內四角貼壁、無環邊穿過內部的矩形不是「在環內」。between 把足跡定在槽內 → 槽內 cell 非合法跨距。
 # M59 殺手(拿掉矩形中心必須在環內的檢查);後兩個是貼槽邊但真的在內的對照組。
 {'scene': '_ax_i5_notch_cell_corners_on_ring.scene', 'expect': 'reject', 'error': 'between 指名的兩端之間沒有合法跨距'},
 {'scene': '_ax_i5_notch_floor_flush_inside.scene', 'expect': 'accept', 'lengths': [100]},
 {'scene': '_ax_i5_notch_wall_flush_inside.scene', 'expect': 'accept', 'lengths': [100]},
 # M08 殺手:四角在環上、中心在環內、但槽底邊穿過內部的 cell 只有「環邊穿入開內部」擋得下(合法跨距被槽切成兩段)。
 {'scene': '_ax_i5_notch_edge_cuts_interior.scene', 'expect': 'reject', 'error': '跨距歧義'},
 {'scene': '_edge_dir_violation.scene', 'expect': 'reject', 'error': '平行'},
 {'scene': '_edge_free.scene', 'expect': 'reject', 'error': '自由邊'},
 {'scene': '_edge_freeze.scene', 'expect': 'reject', 'lengths': [1800], 'error': 'I8a'},
 # 與上面成對:那個測「不預覽就直接改會被擋」,這個測 I8a 的正向路徑
 # 「preview → confirm → 真的套用」。R2「零違規且使用者確認才提交」
 # 先前完全沒有夾具驗證過(GEO-126 稽核發現)。
 {'scene': '_edge_i8a_confirm.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960]},
 {'scene': '_edge_grid_at_border.scene', 'expect': 'reject', 'error': '沒有任何合法跨距'},
 {'scene': '_edge_grid_overflow.scene', 'expect': 'reject', 'error': '座標超過上限'},
 {'scene': '_edge_grid_twoline.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960, 2960, 1973]},
 {'scene': '_test_grid_series.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960, 2960, 1973]},
 {'scene': '_edge_grid_series_step0.scene', 'expect': 'reject', 'error': 'series 的間距必須大於 0'},
 {'scene': '_edge_grid_series_count0.scene', 'expect': 'reject', 'error': 'series 的條數必須至少 1'},
 {'scene': '_edge_grid_series_out.scene', 'expect': 'reject', 'error': '落在承載面外接範圍內'},
 {'scene': '_test_grid_redeclare.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960]},
 {'scene': '_test_grid_redeclare_series.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960]},
 {'scene': '_edge_grid_locked_other_axis.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960]},
 {'scene': '_edge_grid_locked.scene', 'expect': 'reject', 'error': 'I8a'},
 {'scene': '_edge_grid_locked_shrink.scene', 'expect': 'reject', 'error': 'I8a'},
 {'scene': '_test_grid_panel.scene',
  'expect': 'accept',
  'lengths': [3600, 3600, 2960, 2960],
  'contains': ['角材原點：(424, 20, 2500)', '角材原點：(3364, 20, 2500)']},
 {'scene': '_edge_grid_panel_from.scene',
  'expect': 'accept',
  'lengths': [3600, 3600, 2960],
  'contains': ['角材原點：(1424, 20, 2500)']},
 {'scene': '_edge_grid_panel_empty.scene', 'expect': 'accept', 'lengths': []},
 {'scene': '_edge_grid_panel_index8.scene', 'expect': 'reject', 'error': '本軸共 8 條'},
 {'scene': '_edge_grid_panel_empty_place.scene', 'expect': 'reject', 'error': '本軸共 0 條'},
 {'scene': '_edge_grid_panel_odd_gap.scene', 'expect': 'accept', 'error': '縫寬必須是偶數', 'lengths': []},
 {'scene': '_edge_grid_panel_overflow.scene', 'expect': 'reject', 'error': '超過單軸上限'},
 {'scene': '_mut_grid_panel_edge.scene', 'expect': 'reject', 'error': '本軸共 7 條'},
 {'scene': '_edge_grid_panel_shrink.scene', 'expect': 'reject', 'error': 'I8a'},
 {'scene': '_edge_hole_anchor.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960, 2960, 2763]},
 {'scene': '_edge_hole_bottom.scene', 'expect': 'accept', 'lengths': [3960, 3000, 3000]},
 {'scene': '_edge_rect_only.scene', 'expect': 'reject', 'error': 'V_CUT_PRIORITY'},
 {'scene': '_edge_rect_stops.scene', 'expect': 'accept', 'lengths': [3000, 3000, 3960, 3960, 980]},
 {'scene': '_edge_stop_ambiguous.scene', 'expect': 'accept', 'lengths': [3000, 3000, 3960, 3960, 1960]},
 {'scene': '_test_between.scene', 'expect': 'accept', 'lengths': [3000, 3000, 3960, 3960, 1960]},
 {'scene': '_edge_between_free.scene', 'expect': 'reject', 'error': '自由邊'},
 {'scene': '_edge_between_blocked.scene', 'expect': 'reject', 'error': '沒有合法跨距'},
 {'scene': '_edge_between_conflict.scene', 'expect': 'reject', 'error': '不能同時寫'},
 {'scene': '_edge_between_badref.scene', 'expect': 'reject', 'error': '擋面參照只認得'},
 {'scene': '_role_between_priority.scene', 'expect': 'reject', 'error': 'V_CUT_PRIORITY'},
 {'scene': '_edge_straddle.scene', 'expect': 'reject', 'error': '端面懸空'},
 {'scene': '_edge_two_holes.scene', 'expect': 'reject', 'error': '邊界面輪廓不合法'},
 {'scene': '_edge_upper_seg.scene', 'expect': 'accept', 'lengths': [4000, 4000, 1173]},
 {'scene': '_mut_notch_straddle.scene', 'expect': 'reject', 'error': 'R6'},
 {'scene': '_mut_reval_free_hole.scene', 'expect': 'reject', 'error': '重宣告後有物件失效'},
 {'scene': '_mut_through_boundary.scene', 'expect': 'accept', 'lengths': [4000, 1180]},
 {'scene': '_mut_free_hole_end.scene', 'expect': 'reject', 'error': '自由邊'},
 {'scene': '_mut_edge_touch_only.scene', 'expect': 'reject', 'error': 'D7'},
 {'scene': '_mut_grid_dup.scene', 'expect': 'reject', 'error': '嚴格遞增'},
 {'scene': '_mut_zero_len.scene', 'expect': 'reject', 'error': '大於 0'},
 {'scene': '_mut_neg_hole_ref.scene', 'expect': 'reject', 'error': '邊參照'},
 {'scene': '_role_axis_second_primary.scene', 'expect': 'reject', 'error': 'V_PRIMARY_AXIS'},
 {'scene': '_role_axis_boundary_first.scene', 'expect': 'reject', 'error': 'V_PRIMARY_AXIS'},
 {'scene': '_role_axis_fallback.scene', 'expect': 'reject', 'error': 'V_PRIMARY_AXIS'},
 {'scene': '_role_priority_convex.scene', 'expect': 'reject', 'error': 'R6'},
 {'scene': '_role_priority_ext_primary.scene', 'expect': 'reject', 'error': '角材 5（優先級 2）端面頂到角材 4（優先級 2）'},
 {'scene': '_role_priority_mutant.scene', 'expect': 'reject', 'error': 'V_EXTENSION：非 boundary 角材（1）'},
 {'scene': '_role_rc_boundary_ok.scene', 'expect': 'accept', 'lengths': [4000, 4000]},
 {'scene': '_role_rc_custom_reject.scene', 'expect': 'reject', 'error': '端面頂到外輪廓邊（RC）'},
 {'scene': '_role_priority_primary_rc.scene', 'expect': 'reject', 'error': '端面頂到外輪廓邊（RC）'},
 {'scene': '_role_priority_secondary_rc.scene', 'expect': 'reject', 'error': '端面頂到外輪廓邊（RC）'},
 {'scene': '_role_priority_primary_secondary.scene', 'expect': 'reject', 'error': 'V_CUT_PRIORITY'},
 {'scene': '_role_priority_ext_custom.scene', 'expect': 'accept', 'lengths': [4000, 4000, 1946]},
 {'scene': '_role_cover_short.scene', 'expect': 'reject', 'error': 'R6'},
 {'scene': '_role_ext_stop_primary.scene', 'expect': 'accept', 'lengths': [2000, 4000, 2946, 2986]},
 {'scene': '_mut_col_overlap.scene', 'expect': 'reject', 'error': '柱宣告後有物件失效'},
 {'scene': '_mut_col_outside.scene', 'expect': 'reject', 'error': '柱宣告後有物件失效'},
 {'scene': '_mut_beam_diag.scene', 'expect': 'reject', 'error': '走向軸'},
 {'scene': '_mut_col_noz.scene', 'expect': 'reject', 'error': '游離柱'},
 {'scene': '_rc_col_free.scene', 'expect': 'accept'},
 {'scene': '_rc_col_wall.scene', 'expect': 'accept'},
 {'scene': '_rc_col_corner.scene', 'expect': 'accept',
  # GEO-075:封閉六面才印得出三軸內部尺寸。
  'contains': ['內部尺寸 X：4000 mm', '內部尺寸 Y：3000 mm', '內部尺寸 Z：2500 mm']},
 {'scene': '_rc_beam_cross.scene', 'expect': 'accept'},
 {'scene': '_rc_beam_edge.scene', 'expect': 'accept'},
 {'scene': '_ax_i18_norole.scene', 'expect': 'reject', 'error': 'I18'},
 {'scene': '_ax_i18_nopriority.scene', 'expect': 'reject', 'error': 'custom 角色需要 priority'},
 {'scene': '_ax_i18_priority_misuse.scene', 'expect': 'reject', 'error': 'priority 只能配 custom 角色'},
 {'scene': '_ax_i12_auto_with_at.scene', 'expect': 'reject', 'error': 'I12'},
 {'scene': '_ax_i12_explicit_with_atgrid.scene', 'expect': 'reject', 'error': 'D7'},
 {'scene': '_ax_i9_orphan_timber.scene', 'expect': 'reject', 'error': '角材 2 沒有 place'},
 {'scene': '_ax_i9_forward_ref.scene', 'expect': 'reject', 'error': 'place 指的角材不存在'},
 {'scene': '_ax_i1_frame_degenerate.scene', 'expect': 'reject', 'error': 'u 軸與 v 軸必須互相垂直'},
 {'scene': '_ax_i4_empty_space.scene', 'expect': 'accept', 'contains': ['空間 ID：1', '狀態：部分']},
 {'scene': '_ax_i7_guide_out_of_range.scene', 'expect': 'accept'},
 {'scene': '_ax_i16_beam_outside.scene', 'expect': 'reject', 'error': '樑宣告後有物件失效'},
 {'scene': '_ax_i17_delete_space.scene', 'expect': 'accept'},
 {'scene': '_ax_r20_delete_cascade.scene', 'expect': 'reject', 'error': 'I8a'},
 {'scene': '_ax_d12_i14_canvas.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960]},
 {'scene': '_ax_i14_canvas_missing.scene', 'expect': 'reject', 'error': 'canvas-pos 指的物件不存在'},
 {'scene': '_ax_r08_snapshot.scene',
  'expect': 'accept',
  'contains': ['孔 #0', '(1000, 1000) -> (1400, 1000)']},
 {'scene': '_ax_r09_unplaced.scene', 'expect': 'reject', 'error': '未放置的面不能套用投影'},
 {'scene': '_ax_r10_hole_straddles_cut.scene', 'expect': 'reject', 'error': '套用投影後有物件失效'},
 {'scene': '_ax_r10_hole_follows_piece.scene',
  'expect': 'accept',
  'contains': ['孔 #0', '(800, 1000) -> (1200, 1000)']},
 {'scene': '_ax_r12_prefix_col.scene', 'expect': 'accept', 'contains': ['孔 #0']},
 {'scene': '_ax_r12_prefix_beam.scene', 'expect': 'accept', 'not_contains': ['孔 #0']},
 {'scene': '_ax_r13_anchor_lost.scene', 'expect': 'reject', 'error': '拆分後參考線/網格/角材失去承載面'},
 {'scene': '_ax_r13_anchor_follows.scene', 'expect': 'accept', 'lengths': []},
 {'scene': '_ax_r14_straddles_cut.scene', 'expect': 'reject', 'error': '投影項橫跨拆分線'},
 {'scene': '_ax_r15_missing_item.scene', 'expect': 'reject', 'error': 'apply-proj 的項目在此面上不存在'},
 {'scene': '_ax_r16_top_drop.scene', 'expect': 'accept',
  # GEO-075:top_drop 後 Y 軸少一面 → 只印得出 X/Z,Y 不猜(R3)。
  'contains': ['局部範圍：U=[0,4000]，V=[0,2100]', '內部尺寸 X：4000 mm', '內部尺寸 Z：2500 mm'],
  'not_contains': ['內部尺寸 Y']},
 {'scene': '_ax_r16_not_full_span.scene', 'expect': 'reject', 'error': '整段降低的矩形未跨滿輪廓'},
 {'scene': '_ax_r17_wall_column_face.scene',
  'expect': 'accept',
  'contains': ['承載面原點：(400, 0, 0)', '成員邊界面：1 2 3 4 6']},
 {'scene': '_edge_gridref_wrong_face.scene', 'expect': 'reject', 'error': 'I13'},
 {'scene': '_edge_gridref_wrong_axis.scene', 'expect': 'reject', 'error': 'I13'},
 {'scene': '_edge_gridref_midline.scene', 'expect': 'reject', 'error': 'I12'},
 {'scene': '_edge_gridref_no_support.scene', 'expect': 'reject', 'error': 'V_CUT_PRIORITY'},
 {'scene': '_edge_place_through_short.scene', 'expect': 'reject', 'error': 'place 缺少長度方向與深度側'},
 {'scene': '_edge_i19_place_order.scene', 'expect': 'reject', 'error': 'V_CUT_PRIORITY'},
 {'scene': '_wit_d2_wall_frame.scene', 'expect': 'accept', 'lengths': [2500, 2500, 3960]},
 {'scene': '_wit_d6_guide_segments.scene', 'expect': 'accept',
  'contains': ['參考線 1（段 0）：(2000, 0) -> (2000, 1200)', '參考線 1（段 1）：(2000, 1800) -> (2000, 3000)', '參考線 2：（落在有效區域之外，無線段）']},
 {'scene': '_wit_d6c_datum_shared.scene', 'expect': 'accept',
  'contains': ['參考線 1：(1500, 0) -> (1500, 3000)', '參考線 2：(1500, 0) -> (1500, 2500)', '參考線 3：(0, 1500) -> (3000, 1500)']},
 {'scene': '_wit_i13_odd_width.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2960],
  'contains': ['vertex[0] = (1014, 20, 2500)', 'vertex[1] = (987, 20, 2500)']},
 {'scene': '_wit_r6_span_cells.scene', 'expect': 'accept', 'lengths': [4000, 4000, 1180, 1180, 2960]},
 {'scene': '_wit_r19_edge_primary_2560.scene', 'expect': 'accept', 'lengths': [4000, 4000, 2560, 2560, 2560]},
 # GEO-041:空間建構的七種失敗原本共用一句話,現在各自分類。
 {'scene': '_ax_i4_missing_boundary.scene', 'expect': 'reject', 'error': '邊界面 99 不存在'},
 {'scene': '_ax_i4_duplicate_boundary.scene', 'expect': 'reject', 'error': '邊界面 1 被宣告兩次'},
 {'scene': '_ax_i4_no_carrier.scene', 'expect': 'reject', 'error': '沒有承載面'},
 # GEO-172 M10 殺手：孔頂點 (320,250) 落在角材矩形下邊界 v=250 上（貼邊允許，不算相交）。
 {'scene': '_ax_i5_hole_vertex_touches_rect_edge.scene', 'expect': 'accept', 'lengths': [120]},
 # M16 殺手(hi 側):終點壓在孔邊擋面 u 範圍的 hi 端外 → 端面懸空(D11 / R6(d))。
 {'scene': '_edge_straddle_hi.scene', 'expect': 'reject', 'error': '端面懸空'},
 # M24 殺手:合法區間與 at-face 引用邊範圍只相接於一點 → 不算重疊(R6(c) / I11 用語)。
 {'scene': '_edge_face_touch_only.scene', 'expect': 'reject', 'error': '都不接觸引用的邊'},
 # #240 P-143(看板任務 29):把 S7「I5 不得相交」與 S1「R18 凹角」的規則釘成核心場景。
 # 放在清單最後是有意的(#295 審查):mutate.py 的 killed_by 只存 TESTS 順序的前 5 個失敗夾具,
 # 放前面會把 M05–M08 等舊突變帳本裡舊夾具的牙齒擠掉。放最後,舊夾具在 killed_by 的名次不變;
 # 殺手不足 5 個的舊突變會在尾端補上新場景(如 M02、M16、M28)。
 # M87/M88 的殺手很少(p8、p8b、_role_priority_mutant),仍會列在 killed_by 裡;M86 本來就被八十多個場景殺,改由舊夾具列名。
 #
 # S7 三層:同一支 20×20、同一間 4000×3000 的房,各釘一條規則。
 #   (a) 中線 v=10,足跡 v∈[0,20] 貼齊底牆、完全在內 → 接受(I5 閉區域:貼齊不算越界)。
 #   (b) 中線 v=9,足跡 v∈[-1,19] 穿出底牆 1 mm → I5 拒絕;診斷帶 R6/I5/I6(沿線每個 cell 都不 ⊆ 有效範圍)。
 #   (c) 位置同 (a)、角色改 primary → 仍通過 I5,但端面頂外輪廓 → I19 V_CUT_PRIORITY(貼齊是否合法不歸 I5 管)。
 # M86 殺手 = (a):segment2_crosses_rect_interior 的開內部判定拿掉,貼齊的牆邊被誤判成穿入 → 誤拒。
 # (b) 穿出的角點 (0,-1) 落在環外,擋它的是 poly_contains_rect 的「四角須在環內」;
 #   「環邊穿入開內部」那一道(拿掉它 = M08)的牙齒在 _ax_i5_notch_edge_cuts_interior,不在這三層。
 {'scene': '_s7a_flush_inside_accept.scene', 'expect': 'accept', 'lengths': [4000],
  'contains': ['角材原點：(0, 0, 2500)', 'vertex[1] = (0, 20, 2500)']},
 {'scene': '_s7b_poke_out_1mm_i5_reject.scene', 'expect': 'reject', 'error': 'R6/I5/I6 timber 1: 中線上沒有任何合法跨距'},
 {'scene': '_s7c_non_boundary_end_on_outline_cut_priority.scene', 'expect': 'reject',
  'error': 'V_CUT_PRIORITY：角材 1 端面頂到外輪廓邊（RC）'},
 # S1 凹角:#240 P-143 續的原生探針(main 1c807511 實跑)p3/p9 接受、p4/p8 拒絕。
 # p3/p9 是下角材模板依賴的兩個合法表示法(R19(e):凹角內邊的邊界材可延伸過凹角、停在內部主支側面);
 # p4/p8 是對照:primary 不能停在延伸段上(I22 以優先級 2 計 → V_CUT_PRIORITY)、
 # primary 整支穿過凹角即有「超出定位邊」的延伸段,而延伸段只有 boundary 可有 → V_EXTENSION。
 # M87 殺手 = p8:拿掉 timber_end_face_check 裡 V_EXTENSION 的拒絕;M88 殺手 = p8b:只拿掉「超出終點」那一半。
 {'scene': '_s1_p3_alcove_side_boundary_extension_accept.scene', 'expect': 'accept',
  'lengths': [4000, 4000, 2946, 1287, 1287]},
 {'scene': '_s1_p4_alcove_wall_primary_cut_priority.scene', 'expect': 'reject',
  'error': 'V_CUT_PRIORITY：角材 6（優先級 2）端面頂到角材 4（優先級 2）側面'},
 # 只釘前綴:I22 要求訊息另指名定位邊與超出區間,核心日後補上時不該誤紅。
 {'scene': '_s1_p8_l_room_primary_through_reflex_extension.scene', 'expect': 'reject',
  'error': 'V_EXTENSION：非 boundary 角材（3）'},
 # p8 的高端鏡像:M88 殺手(V_EXTENSION 只驗起點那一半)。
 {'scene': '_s1_p8b_l_room_primary_through_reflex_extension_hi.scene', 'expect': 'reject',
  'error': 'V_EXTENSION：非 boundary 角材（3）'},
 {'scene': '_s1_p9_l_room_custom_inner_wall_accept.scene', 'expect': 'accept',
  'lengths': [5000, 3200, 4746, 2236, 1773]},
]


LEN_RE = re.compile(r"L=(\d+)")


def run_one(exe: str, spec: dict) -> str:
    scene = ROOT / spec["scene"]
    if spec.get("expect") not in ("accept", "reject"):
        return "INFRA invalid test expectation"
    if spec["expect"] == "reject" and not spec.get("error"):
        return "INFRA rejection requires an explicit expected diagnostic"
    if not scene.is_file():
        return f"INFRA missing fixture: {scene}"
    proc = subprocess.run(
        [exe, "--scene", str(scene), "--no-window"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=30,
    )
    out, err = proc.stdout, proc.stderr
    # Domain rejection is exit 1. A signal, loader error or Windows crash is
    # not evidence that the requested geometric rule rejected this scene.
    if proc.returncode not in (0, 1):
        return f"INFRA abnormal executable exit {proc.returncode}: {err[:200]}"
    ok = proc.returncode == 0

    if spec["expect"] == "accept":
        if not ok:
            first = err.strip().splitlines()[0] if err.strip() else "(無錯誤訊息)"
            return f"FAIL 應接受但拒絕: {first}"
        lengths = [int(m) for m in LEN_RE.findall(out)]
        if "lengths" in spec and lengths != spec["lengths"]:
            return f"FAIL 長度不符: 期望 {spec['lengths']} 實得 {lengths}"
        for needle in spec.get("contains", []):
            if needle not in out:
                return f"FAIL 輸出缺少「{needle}」"
        # 有些夾具主張的是「什麼都沒發生」(例如 R12:條帶項沒帶 cut-strip
        # 就不動幾何)。那種主張只能用「不該出現」來驗,accept 本身驗不到。
        for needle in spec.get("not_contains", []):
            if needle in out:
                return f"FAIL 輸出不該有「{needle}」"
        return "ok"

    # expect == reject
    if ok:
        lengths = LEN_RE.findall(out)
        return f"FAIL 應拒絕但接受 (L={lengths})"
    first = err.strip().splitlines()[0] if err.strip() else "(無錯誤訊息)"
    diagnostics = re.findall(r"^" + re.escape(str(scene)) + r":(?:\d+:)?\s*(.*)$", err, re.MULTILINE)
    if not any(spec["error"] in diagnostic for diagnostic in diagnostics):
        return f"FAIL 錯誤不符: 期望含「{spec['error']}」實得「{first}」"
    return "ok"


def main() -> int:
    exe = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "cg_new.exe")
    results = []
    for spec in TESTS:
        try:
            verdict = run_one(exe, spec)
        except subprocess.TimeoutExpired:
            verdict = "INFRA 逾時"
        except Exception as exc:  # noqa: BLE001
            verdict = f"INFRA 例外 {exc}"
        status = "pass" if verdict == "ok" else "infrastructure" if verdict.startswith("INFRA") else "fail"
        print(f"{spec['scene']:<34} {'PASS' if status == 'pass' else verdict}")
        oracle = "rejection-diagnostic" if spec["expect"] == "reject" else "geometry-output" if any(key in spec for key in ("lengths", "contains")) else "acceptance-and-absence" if spec.get("not_contains") else "acceptance-only"
        results.append({"scene": spec["scene"], "status": status, "detail": verdict, "oracle": oracle})
    counts = {key: sum(row["status"] == key for row in results) for key in ("pass", "fail", "infrastructure")}
    print(f"\n{counts['pass']}/{len(TESTS)} 通過；斷言失敗 {counts['fail']}；環境／執行失敗 {counts['infrastructure']}")
    oracle_counts = {key: sum(row["oracle"] == key for row in results) for key in sorted({row["oracle"] for row in results})}
    print("Oracle coverage: " + json.dumps(oracle_counts, ensure_ascii=False))
    print("GEOMETRY_TEST_RESULT " + json.dumps({"schema": "geometry-native-tests/1", "total": len(TESTS), "counts": counts, "oracle_counts": oracle_counts, "cases": results}, ensure_ascii=False))
    return 2 if counts["infrastructure"] or not results else 1 if counts["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
