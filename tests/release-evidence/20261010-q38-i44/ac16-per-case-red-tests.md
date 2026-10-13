# AC16 故障注入：--explore 逐案例轉紅清單

來源：`q38-mutations-explore.json`（`python3 tests/section_profile_mutation_check.py --explore`，每個案例跑整個測試類別、不套用殺手斷言）。
「紅燈測試」是該案例實際失敗的測試方法（FAIL＝斷言失敗，ERROR＝錯誤）。
「對應提案 AC」是**人工讀測試內容**對到 `SECTION-PROFILE-EXTRUSION-PROPOSAL.md` §AC 表的結果，不是機器產物：測試方法本身不帶 AC 編號
（只有方法名 `ac01_03_08`、`ac09` 與訊息裡的 `AC10`；方法名 `..._ac24_...` 指的不是提案 AC24）。
`=` 表示該測試用的就是提案該列的場景；`~` 表示場景相似但座標、輪廓或尺寸不同（例如提案 AC06 用 (20,0)，測試用 u=26）。

| 案例 | 組 | 條號 | 突變 | 判定 | 紅燈測試數 | 紅燈測試所含的提案 AC（方法層級，偏寬） |
|---|---|---|---|---|---|---|
| SPM01 | native | I44 | drop the member-in-profile containment check | killed | 4 | AC03, AC04~, AC05~, AC06~, AC12, AC13~, AC18, AC19~ |
| SPM02 | native | I45 | drop the member-overlap check | killed | 3 | AC06~, AC07, AC24~ |
| SPM03 | native | R36 | u overlap uses <= : edge-sharing members become overlapping | killed | 2 | AC06~, AC07, AC24~ |
| SPM04 | native | R36 | v overlap uses <= : members touching along v become overlapping | killed | 1 | AC06~, AC07, AC24~ |
| SPM05 | native | I46/D40 | panel width w < 915 becomes w <= 915 | killed | 1 | AC20, AC21, AC22, AC25~, AC26 |
| SPM06 | native | I46 | panel width lower bound 1 becomes 0 | killed | 1 | AC20, AC21, AC22, AC25~, AC26 |
| SPM07 | native | D40 | panel spec identity is no longer checked | killed | 1 | AC03, AC04~, AC13~, AC19~ |
| SPM08 | native | D40 | spec thickness 6 becomes 7 | killed | 1 | AC20, AC21, AC22, AC25~, AC26 |
| SPM09 | native | D40 | spec w_max 915 becomes 914 | killed | 1 | AC20, AC21, AC22, AC25~, AC26 |
| SPM10 | native | I43 | drop the outline validity check | killed | 1 | AC03, AC04~, AC13~, AC19~ |
| SPM11 | native | D37 | run length accepts a D26 material source | killed | 1 | （無對應提案 AC） |
| SPM12 | native | D36 | material A/B field identity is no longer enforced | killed | 1 | （無對應提案 AC） |
| SPM13 | native | I51 | scene records no longer need the section-profile/1 declaration | killed | 1 | AC14 |
| SPM14 | native | I46 | timber orientation is not validated | killed | 1 | AC03, AC04~, AC13~, AC19~ |
| SPM15 | native | I46 | panel orientation is not validated | killed | 1 | AC03, AC04~, AC13~, AC19~ |
| SPM16 | native | R38 | V = +up instead of -up | killed | 3 | AC10=/~, AC14~ |
| SPM17 | native | R38 | negative directions (-u,-v) lose their sign | killed | 1 | AC10~ |
| SPM18 | native | R38 | dir +u/-u and +v/-v pick the wrong host axis | killed | 4 | AC10=/~, AC13~, AC14~ |
| SPM19 | native | I48 | p,q may lie outside the host range | killed | 2 | AC13~ |
| SPM20 | native | I48 | up need not be perpendicular to the run direction | killed | 1 | AC13~ |
| SPM21 | native | I48/D1 | simple-placement origin is not range-checked | killed | 1 | AC13~ |
| SPM22 | native | R38 | origin x component swaps p and q | killed | 3 | AC10=/~, AC14~ |
| SPM23 | native | D38 | advanced->simple conversion ignores the host plane | killed | 1 | AC11 |
| SPM24 | native | D38 | advanced->simple conversion accepts any V as up | equivalent | 0 | — |
| SPM25 | native | D38 | advanced->simple conversion takes the last host direction regardless of N | killed | 3 | AC10~, AC11 |
| SPM26 | native | I49 | PROFILE_CONTACT_LOST is never reported | killed | 1 | AC12, AC18 |
| SPM27 | native | I44 | outside-region split drops the right-hand remainder | killed | 4 | AC03, AC04~, AC05~, AC06~, AC12, AC13~, AC18, AC19~ |
| SPM28 | native | I49 | a member may reference a deleted profile | killed | 1 | （無對應提案 AC） |
| SPM29 | native | I49 | a run may reference a deleted profile | killed | 1 | （無對應提案 AC） |
| SPM30 | native | I47/D1 | generated run vertices are not range-checked | killed | 1 | AC09, AC13~ |
| SPM31 | native | R36 | A-v / thickness-u swap width and height the wrong way round | killed | 15 | AC01, AC02, AC03, AC04~, AC05~, AC06~, AC07, AC08, AC09, AC10=/~, AC12, AC13~, AC14~, AC15, AC18, AC19~, AC20, AC21, AC22, AC24~, AC25~, AC26 |
| SPM32 | native | D36 | panel orientation thickness-u is read as thickness-v | killed | 1 | AC20, AC21, AC22, AC25~, AC26 |
| SPM33 | native | D40/R37 | the 1830 mm sheet length is misused as an upper bound for the run length | killed | 15 | AC01, AC02, AC03, AC06~, AC08, AC09, AC10=/~, AC11, AC12, AC13~, AC14=/~, AC15, AC18, AC20, AC21, AC22, AC25~, AC26 |
| SPM34 | native | I51 | scene load accepts a duplicate profile id | killed | 1 | AC14 |
| SPM35 | native | I49 | section-profile records may be injected line by line outside an atomic load | killed | 1 | AC14 |
| SPM41 | native | I44 | back to poly_contains_rect: a rectangle exactly filling a notch counts as contained | killed | 1 | AC05~ |
| SPM42 | native | I47/D1 | only the start vertex of a run is range-checked, not the far end | killed | 1 | AC09, AC13~ |
| SPM36 | model | R37 | the reference envelope becomes the bounding rectangle of the outline (L shape lost) | killed | 2 | AC08~, AC14~ |
| SPM37 | model | R39 | the reference envelope is counted as material volume | killed | 3 | AC08~, AC14~ |
| SPM38 | model | R37/D40 | a panel is cut at the 1830 mm sheet length | killed | 1 | AC26 |
| SPM39 | model | R36/R37 | member rectangles are read with u and v swapped | killed | 6 | AC08~, AC09, AC10~, AC26 |
| SPM40 | model | D39 | an unplaced (local) run is cut by the world grid | killed | 11 | AC08~, AC14~, AC26 |

## 逐案例紅燈測試

### SPM01（native，I44）drop the member-in-profile containment check

判定 `killed`。
- FAIL `test_all_violations_exact_regions_and_retained_rectangles` → AC04 ~, AC05 ~, AC06 ~
  - 訊息：`AssertionError: 'V_PROFILE_OUTSIDE' not found in '{"token": 2, "valid": false, "revision": 12, "diagnosticsComplete": true, "validationStrategy": "all-section-profile-violations", "before": {"capabilities": ["engineering-spec/1", `
- FAIL `test_concave_not_four_corners_and_winding` → AC05 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'V_PROFILE_OUTSIDE' but the candidate was accepted: {'token': 2, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violati`
- FAIL `test_profile_geometry_and_coordinate_rejections` → AC03 = (reject half), AC04 ~, AC13 ~, AC19 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'V_PROFILE_OUTSIDE' but the candidate was accepted: {'token': 10, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violat`
- FAIL `test_shrink_reject_and_expand_loses_right_contact` → AC12, AC18
  - 訊息：`AssertionError: True is not false : expected rejection 'V_PROFILE_OUTSIDE' but the candidate was accepted: {'token': 2, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violati`

### SPM02（native，I45）drop the member-overlap check

判定 `killed`。
- FAIL `test_maximum_pair_diagnostics_and_copied_host_capacity_roundtrip` → AC06 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'V_PROFILE_OVERLAP' but the candidate was accepted: {'token': 2, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violati`
- FAIL `test_named_sources_rebuild_and_explicit_dependency_transaction` → 無對應提案 AC
  - 訊息：`AssertionError: True is not false : expected rejection 'V_PROFILE_OVERLAP' but the candidate was accepted: {'token': 2, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violati`
- FAIL `test_touch_edges_points_and_cross_kind_overlap` → AC06 ~, AC07, AC24 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'V_PROFILE_OVERLAP' but the candidate was accepted: {'token': 3, 'valid': True, 'revision': 13, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violati`

### SPM03（native，R36）u overlap uses <= : edge-sharing members become overlapping

判定 `killed`。
- FAIL `test_named_sources_rebuild_and_explicit_dependency_transaction` → 無對應提案 AC
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_touch_edges_points_and_cross_kind_overlap` → AC06 ~, AC07, AC24 ~
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 2, 'valid': False, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`

### SPM04（native，R36）v overlap uses <= : members touching along v become overlapping

判定 `killed`。
- FAIL `test_touch_edges_points_and_cross_kind_overlap` → AC06 ~, AC07, AC24 ~
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 2, 'valid': False, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`

### SPM05（native，I46/D40）panel width w < 915 becomes w <= 915

判定 `killed`。
- FAIL `test_panel_strict_width_fixed_spec_and_long_run` → AC20, AC21, AC22, AC25 ~, AC26
  - 訊息：`AssertionError: True is not false : expected rejection 'V_PANEL_WIDTH' but the candidate was accepted: {'token': 3, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations'`

### SPM06（native，I46）panel width lower bound 1 becomes 0

判定 `killed`。
- FAIL `test_panel_strict_width_fixed_spec_and_long_run` → AC20, AC21, AC22, AC25 ~, AC26
  - 訊息：`AssertionError: True is not false : expected rejection 'V_PANEL_WIDTH' but the candidate was accepted: {'token': 2, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations'`

### SPM07（native，D40）panel spec identity is no longer checked

判定 `killed`。
- FAIL `test_profile_geometry_and_coordinate_rejections` → AC03 = (reject half), AC04 ~, AC13 ~, AC19 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'panel requires calcium-silicate-6' but the candidate was accepted: {'token': 13, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-sectio`

### SPM08（native，D40）spec thickness 6 becomes 7

判定 `killed`。
- FAIL `test_panel_strict_width_fixed_spec_and_long_run` → AC20, AC21, AC22, AC25 ~, AC26
  - 訊息：`AssertionError: Lists differ: [0, 0, 914, 6] != [0, 0, 914, 7]`

### SPM09（native，D40）spec w_max 915 becomes 914

判定 `killed`。
- FAIL `test_panel_strict_width_fixed_spec_and_long_run` → AC20, AC21, AC22, AC25 ~, AC26
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`

### SPM10（native，I43）drop the outline validity check

判定 `killed`。
- FAIL `test_profile_geometry_and_coordinate_rejections` → AC03 = (reject half), AC04 ~, AC13 ~, AC19 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'I43' but the candidate was accepted: {'token': 3, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before'`

### SPM11（native，D37）run length accepts a D26 material source

判定 `killed`。
- FAIL `test_parameter_zero_ids_types_and_fixed_material_sources_roundtrip` → 無對應提案 AC
  - 訊息：`AssertionError: True is not false : expected rejection 'unsupported dimension source' but the candidate was accepted: {'token': 4, 'valid': True, 'revision': 14, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-prof`

### SPM12（native，D36）material A/B field identity is no longer enforced

判定 `killed`。
- FAIL `test_parameter_zero_ids_types_and_fixed_material_sources_roundtrip` → 無對應提案 AC
  - 訊息：`AssertionError: 'D36' not found in '{"token": 3, "valid": false, "revision": 14, "diagnosticsComplete": true, "validationStrategy": "all-section-profile-violations", "before": {"capabilities": ["engineering-spec/1", "parameters/1"`

### SPM13（native，I51）scene records no longer need the section-profile/1 declaration

判定 `killed`。
- FAIL `test_exact_dump_load_zero_ids_empty_profile_and_fail_closed` → AC14
  - 訊息：`AssertionError: True is not false : I51: a scene with a missing requires section-profile/1 marker must be rejected`

### SPM14（native，I46）timber orientation is not validated

判定 `killed`。
- FAIL `test_profile_geometry_and_coordinate_rejections` → AC03 = (reject half), AC04 ~, AC13 ~, AC19 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'timber orientation must be A-u or A-v' but the candidate was accepted: {'token': 11, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-se`

### SPM15（native，I46）panel orientation is not validated

判定 `killed`。
- FAIL `test_profile_geometry_and_coordinate_rejections` → AC03 = (reject half), AC04 ~, AC13 ~, AC19 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'panel orientation must be thickness-v or thickness-u' but the candidate was accepted: {'token': 12, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStr`

### SPM16（native，R38）V = +up instead of -up

判定 `killed`。
- FAIL `test_all_cardinal_frames_and_four_host_directions_are_exact` → AC10 ~
  - 訊息：`AssertionError: Lists differ: [0, 0, -1] != [0, 0, 1]`
- FAIL `test_live_host_follow_detach_conversion_and_atomic_delete` → AC10 ~
  - 訊息：`AssertionError: {'val[179 chars]p': '+Z'}, 'profileId': 1}, 'length': 2400, 'c[326 chars]]]}]} != {'val[179 chars]p': '-Z'}, 'profileId': 1}, 'length': 2400, 'c[330 chars]]]}]}`
- FAIL `test_simple_copied_host_ac24_and_fresh_scene_roundtrip` → AC10, AC14 ~
  - 訊息：`AssertionError: {'origin': [1000, 2000, 2700], 'U': [1, 0, 0], 'V': [0, 0, -1], 'N': [0, 1, 0]} != {'origin': [1000, 2000, 2700], 'U': [-1, 0, 0], 'V': [0, 0, 1], 'N': [0, 1, 0]}`

### SPM17（native，R38）negative directions (-u,-v) lose their sign

判定 `killed`。
- FAIL `test_all_cardinal_frames_and_four_host_directions_are_exact` → AC10 ~
  - 訊息：`AssertionError: Lists differ: [-1, 0, 0] != [1, 0, 0]`

### SPM18（native，R38）dir +u/-u and +v/-v pick the wrong host axis

判定 `killed`。
- FAIL `test_all_cardinal_frames_and_four_host_directions_are_exact` → AC10 ~
  - 訊息：`AssertionError: Lists differ: [1, 0, 0] != [0, 1, 0]`
- FAIL `test_live_host_follow_detach_conversion_and_atomic_delete` → AC10 ~
  - 訊息：`AssertionError: {'val[79 chars]': '+v', 'host': {'kind': 'placement', 'placem[431 chars]]]}]} != {'val[79 chars]': '+u', 'host': {'kind': 'placement', 'placem[430 chars]]]}]}`
- FAIL `test_simple_copied_host_ac24_and_fresh_scene_roundtrip` → AC10, AC14 ~
  - 訊息：`AssertionError: {'origin': [1000, 2000, 2700], 'U': [1, 0, 0], 'V': [0, 0, -1], 'N': [0, 1, 0]} != {'origin': [1000, 2000, 2700], 'U': [0, -1, 0], 'V': [0, 0, -1], 'N': [1, 0, 0]}`
- FAIL `test_simple_holes_closed_boundary_vertical_direction_and_invalid_up` → AC13 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'perpendicular' but the candidate was accepted: {'token': 4, 'valid': True, 'revision': 13, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations'`

### SPM19（native，I48）p,q may lie outside the host range

判定 `killed`。
- FAIL `test_live_host_shrink_lists_each_run_and_pending_reads_preserve_token` → 無對應提案 AC
  - 訊息：`AssertionError: True is not false : {'ok': True}`
- FAIL `test_simple_holes_closed_boundary_vertical_direction_and_invalid_up` → AC13 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'outside closed host range' but the candidate was accepted: {'token': 2, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile`

### SPM20（native，I48）up need not be perpendicular to the run direction

判定 `killed`。
- FAIL `test_simple_holes_closed_boundary_vertical_direction_and_invalid_up` → AC13 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'perpendicular' but the candidate was accepted: {'token': 4, 'valid': True, 'revision': 13, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations'`

### SPM21（native，I48/D1）simple-placement origin is not range-checked

判定 `killed`。
- FAIL `test_simple_holes_closed_boundary_vertical_direction_and_invalid_up` → AC13 ~
  - 訊息：`AssertionError: 'origin exceeds D1' not found in '{"token": 7, "valid": false, "revision": 14, "diagnosticsComplete": true, "validationStrategy": "all-section-profile-violations", "before": {"capabilities": ["engineering-spec/1", `

### SPM22（native，R38）origin x component swaps p and q

判定 `killed`。
- FAIL `test_live_host_follow_detach_conversion_and_atomic_delete` → AC10 ~
  - 訊息：`AssertionError: Lists differ: [1000, 2000, 2800] != [2000, 2000, 2800]`
- FAIL `test_live_host_shrink_lists_each_run_and_pending_reads_preserve_token` → 無對應提案 AC
  - 訊息：`AssertionError: Lists differ: [1200, 2000, 2700] != [2000, 2000, 2700]`
- FAIL `test_simple_copied_host_ac24_and_fresh_scene_roundtrip` → AC10, AC14 ~
  - 訊息：`AssertionError: {'origin': [1000, 2000, 2700], 'U': [1, 0, 0], 'V': [0, 0, -1], 'N': [0, 1, 0]} != {'origin': [2000, 2000, 2700], 'U': [1, 0, 0], 'V': [0, 0, -1], 'N': [0, 1, 0]}`

### SPM23（native，D38）advanced->simple conversion ignores the host plane

判定 `killed`。
- FAIL `test_conversion_reports_all_unsatisfied_conditions_and_zero_writes` → AC11
  - 訊息：`AssertionError: 'origin not in host plane' not found in '{"token": 2, "valid": false, "revision": 12, "diagnosticsComplete": true, "validationStrategy": "all-section-profile-violations", "before": {"capabilities": ["engineering-sp`

### SPM24（native，D38）advanced->simple conversion accepts any V as up

判定 `equivalent`。
- 沒有任何測試轉紅（整個測試類別零失敗）。

### SPM25（native，D38）advanced->simple conversion takes the last host direction regardless of N

判定 `killed`。
- FAIL `test_all_cardinal_frames_and_four_host_directions_are_exact` → AC10 ~
  - 訊息：`AssertionError: {'val[78 chars]r': '+u', 'host': {'frame': {'N': '+Z', 'U': '[388 chars]: []} != {'val[78 chars]r': '-v', 'host': {'frame': {'N': '+Z', 'U': '[389 chars]: []}`
- FAIL `test_conversion_reports_all_unsatisfied_conditions_and_zero_writes` → AC11
  - 訊息：`AssertionError: 'N not a host-plane direction' not found in '{"token": 2, "valid": false, "revision": 12, "diagnosticsComplete": true, "validationStrategy": "all-section-profile-violations", "before": {"capabilities": ["engineerin`
- FAIL `test_live_host_follow_detach_conversion_and_atomic_delete` → AC10 ~
  - 訊息：`AssertionError: {'val[78 chars]r': '+v', 'host': {'kind': 'placement', 'place[431 chars]]]}]} != {'val[78 chars]r': '-v', 'host': {'kind': 'placement', 'place[429 chars]]]}]}`

### SPM26（native，I49）PROFILE_CONTACT_LOST is never reported

判定 `killed`。
- FAIL `test_shrink_reject_and_expand_loses_right_contact` → AC12, AC18
  - 訊息：`AssertionError: {'code': 'PROFILE_CONTACT_LOST', 'clause': 'I49', 'memberId': 2, 'profileId': 1} not found in []`

### SPM27（native，I44）outside-region split drops the right-hand remainder

判定 `killed`。
- FAIL `test_all_violations_exact_regions_and_retained_rectangles` → AC04 ~, AC05 ~, AC06 ~
  - 訊息：`AssertionError: Items in the first set but not the second:`
- FAIL `test_concave_not_four_corners_and_winding` → AC05 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'V_PROFILE_OUTSIDE' but the candidate was accepted: {'token': 3, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violati`
- FAIL `test_profile_geometry_and_coordinate_rejections` → AC03 = (reject half), AC04 ~, AC13 ~, AC19 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'V_PROFILE_OUTSIDE' but the candidate was accepted: {'token': 10, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violat`
- FAIL `test_shrink_reject_and_expand_loses_right_contact` → AC12, AC18
  - 訊息：`AssertionError: True is not false : expected rejection 'V_PROFILE_OUTSIDE' but the candidate was accepted: {'token': 2, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violati`

### SPM28（native，I49）a member may reference a deleted profile

判定 `killed`。
- FAIL `test_named_sources_rebuild_and_explicit_dependency_transaction` → 無對應提案 AC
  - 訊息：`AssertionError: True is not false : expected rejection 'I49' but the candidate was accepted: {'token': 6, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before'`

### SPM29（native，I49）a run may reference a deleted profile

判定 `killed`。
- FAIL `test_named_sources_rebuild_and_explicit_dependency_transaction` → 無對應提案 AC
  - 訊息：`AssertionError: True is not false : expected rejection 'I49' but the candidate was accepted: {'token': 5, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before'`

### SPM30（native，I47/D1）generated run vertices are not range-checked

判定 `killed`。
- FAIL `test_ac09_advanced_axes_and_vertex_range` → AC09, AC13 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'I47/I48/D1' but the candidate was accepted: {'token': 4, 'valid': True, 'revision': 13, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', '`

### SPM31（native，R36）A-v / thickness-u swap width and height the wrong way round

判定 `killed`。
- FAIL `test_ac01_03_08_independent_rectangles_volumes_and_scope` → AC01, AC02, AC03 = (accept half), AC08
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_ac09_advanced_axes_and_vertex_range` → AC09, AC13 ~
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_all_bad_dimension_dependents_are_diagnosed` → 無對應提案 AC
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_atomic_preview_cancel_wrong_kind_stale_undo_redo` → AC15
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 2, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_concave_not_four_corners_and_winding` → AC05 ~
  - 訊息：`AssertionError: Lists differ: [[[40, 40, 60, 100]]] != [[[40, 40, 60, 60]]]`
- FAIL `test_live_host_follow_detach_conversion_and_atomic_delete` → AC10 ~
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 13, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_named_sources_rebuild_and_explicit_dependency_transaction` → 無對應提案 AC
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_panel_strict_width_fixed_spec_and_long_run` → AC20, AC21, AC22, AC25 ~, AC26
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_parameter_zero_ids_types_and_fixed_material_sources_roundtrip` → 無對應提案 AC
  - 訊息：`AssertionError: Lists differ: [0, 0, 33, 27] != [0, 0, 27, 33]`
- FAIL `test_profile_geometry_and_coordinate_rejections` → AC03 = (reject half), AC04 ~, AC13 ~, AC19 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'V_PROFILE_OUTSIDE' but the candidate was accepted: {'token': 10, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violat`
- FAIL `test_shared_parameter_preview_cancel_tokens_and_history_both_domains` → 無對應提案 AC
  - 訊息：`AssertionError: Lists differ: [0, 0, 500, 33] != [0, 0, 33, 500]`
- FAIL `test_shrink_reject_and_expand_loses_right_contact` → AC12, AC18
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_simple_copied_host_ac24_and_fresh_scene_roundtrip` → AC10, AC14 ~
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_touch_edges_points_and_cross_kind_overlap` → AC06 ~, AC07, AC24 ~
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 2, 'valid': False, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_upstream_engineering_and_parameter_failure_still_lists_each_profile_dependent` → 無對應提案 AC
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 14, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`

### SPM32（native，D36）panel orientation thickness-u is read as thickness-v

判定 `killed`。
- FAIL `test_panel_strict_width_fixed_spec_and_long_run` → AC20, AC21, AC22, AC25 ~, AC26
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`

### SPM33（native，D40/R37）the 1830 mm sheet length is misused as an upper bound for the run length

判定 `killed`。
- FAIL `test_ac01_03_08_independent_rectangles_volumes_and_scope` → AC01, AC02, AC03 = (accept half), AC08
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_ac09_advanced_axes_and_vertex_range` → AC09, AC13 ~
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_all_cardinal_frames_and_four_host_directions_are_exact` → AC10 ~
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 2, 'valid': False, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_atomic_preview_cancel_wrong_kind_stale_undo_redo` → AC15
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 2, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_conversion_reports_all_unsatisfied_conditions_and_zero_writes` → AC11
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_each_capacity_rejects_without_partial_writes` → 無對應提案 AC
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 5, 'valid': False, 'revision': 13, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_exact_dump_load_zero_ids_empty_profile_and_fail_closed` → AC14
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_live_host_follow_detach_conversion_and_atomic_delete` → AC10 ~
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 13, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_live_host_shrink_lists_each_run_and_pending_reads_preserve_token` → 無對應提案 AC
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 13, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_maximum_pair_diagnostics_and_copied_host_capacity_roundtrip` → AC06 ~
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 3, 'valid': False, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_named_sources_rebuild_and_explicit_dependency_transaction` → 無對應提案 AC
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_panel_strict_width_fixed_spec_and_long_run` → AC20, AC21, AC22, AC25 ~, AC26
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_shrink_reject_and_expand_loses_right_contact` → AC12, AC18
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_simple_copied_host_ac24_and_fresh_scene_roundtrip` → AC10, AC14 ~
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 1, 'valid': False, 'revision': 11, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`
- FAIL `test_simple_holes_closed_boundary_vertical_direction_and_invalid_up` → AC13 ~
  - 訊息：`AssertionError: False is not true : expected the candidate to be accepted: {'token': 3, 'valid': False, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', 'before': {'capabilities'`

### SPM34（native，I51）scene load accepts a duplicate profile id

判定 `killed`。
- FAIL `test_exact_dump_load_zero_ids_empty_profile_and_fail_closed` → AC14
  - 訊息：`AssertionError: True is not false : I51: a scene with a duplicate profile id record must be rejected`

### SPM35（native，I49）section-profile records may be injected line by line outside an atomic load

判定 `killed`。
- FAIL `test_exact_dump_load_zero_ids_empty_profile_and_fail_closed` → AC14
  - 訊息：`AssertionError: 'preview' unexpectedly found in {'ok': False, 'error': 'line 1: I8a: impact preview required; inspect preview, then confirm token (World unchanged)', 'preview': {'token': 1, 'valid': True, 'command': 'section-profi`

### SPM41（native，I44）back to poly_contains_rect: a rectangle exactly filling a notch counts as contained

判定 `killed`。
- FAIL `test_concave_not_four_corners_and_winding` → AC05 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'V_PROFILE_OUTSIDE' but the candidate was accepted: {'token': 3, 'valid': True, 'revision': 12, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violati`

### SPM42（native，I47/D1）only the start vertex of a run is range-checked, not the far end

判定 `killed`。
- FAIL `test_ac09_advanced_axes_and_vertex_range` → AC09, AC13 ~
  - 訊息：`AssertionError: True is not false : expected rejection 'I47/I48/D1' but the candidate was accepted: {'token': 10, 'valid': True, 'revision': 14, 'diagnosticsComplete': True, 'validationStrategy': 'all-section-profile-violations', `

### SPM36（model，R37）the reference envelope becomes the bounding rectangle of the outline (L shape lost)

判定 `killed`。
- FAIL `test_three_timber_members_and_actual_concave_reference_envelope` → AC08 ~
  - 訊息：`AssertionError: '240000000' != '84960000'`
- FAIL `test_zero_members_and_unused_profiles_are_preserved` → AC14 ~
  - 訊息：`AssertionError: '240000000' != '84960000'`

### SPM37（model，R39）the reference envelope is counted as material volume

判定 `killed`。
- FAIL `test_obj_labels_local_reference_material_and_rejects_mixed_frames` → 無對應提案 AC
  - 訊息：`AssertionError: 'kind envelope; material-volume-mm3 0' not found in '# geometry-axiom orthogonal-model/1\n# units: millimetres; right handed\n# coordinates: local (u,v,w) of profile-run 1; no world position or world up\n# Definiti`
- FAIL `test_three_timber_members_and_actual_concave_reference_envelope` → AC08 ~
  - 訊息：`AssertionError: Tuples differ: ('reference', [], 'envelope', '84960000') != ('reference', [], 'envelope', '0')`
- FAIL `test_zero_members_and_unused_profiles_are_preserved` → AC14 ~
  - 訊息：`AssertionError: '84960000' != '0'`

### SPM38（model，R37/D40）a panel is cut at the 1830 mm sheet length

判定 `killed`。
- ERROR `test_long_panel_is_one_exact_solid_in_both_orientations` → AC26
  - 訊息：`modeling.common.ModelError: Native dimensions and derived exact member volume disagree`

### SPM39（model，R36/R37）member rectangles are read with u and v swapped

判定 `killed`。
- FAIL `test_advanced_native_frame_controls_world_axes_and_bounds` → AC09
  - 訊息：`AssertionError: Lists differ: [[1000, 2000, 2673], [1033, 4400, 2700]] != [[1000, 2000, 2667], [1027, 4400, 2700]]`
- FAIL `test_copied_host_keeps_holes_description_and_no_live_space_dependency` → AC10 ~
  - 訊息：`AssertionError: Lists differ: [[120, 230, 273], [153, 2630, 300]] != [[120, 230, 267], [147, 2630, 300]]`
- FAIL `test_long_panel_is_one_exact_solid_in_both_orientations` → AC26
  - 訊息：`AssertionError: Lists differ: [[0, 0, 0], [6, 914, 2000]] != [[0, 0, 0], [914, 6, 2000]]`
- FAIL `test_simple_live_host_rebuilds_native_frame_and_retains_dependency_grid` → AC10 ~
  - 訊息：`AssertionError: Lists differ: [[20, 30, 2473], [53, 2430, 2500]] != [[20, 30, 2467], [47, 2430, 2500]]`
- FAIL `test_spec_update_preview_cancel_confirm_and_invalid_update_preserve_source` → 無對應提案 AC
  - 訊息：`AssertionError: Lists differ: [[0, 0, 0], [33, 29, 2400]] != [[0, 0, 0], [29, 33, 2400]]`
- FAIL `test_three_timber_members_and_actual_concave_reference_envelope` → AC08 ~
  - 訊息：`AssertionError: Lists differ: [[0, 0, 0], [33, 27, 2400]] != [[0, 0, 0], [27, 33, 2400]]`

### SPM40（model，D39）an unplaced (local) run is cut by the world grid

判定 `killed`。
- ERROR `test_capability_reduction_unknown_capability_and_old_axioms_reject` → 無對應提案 AC
  - 訊息：`modeling.common.ModelError: A section-profile object must produce one complete solid`
- ERROR `test_local_runs_do_not_cut_other_local_or_world_mesh_grids` → AC08 ~
  - 訊息：`modeling.common.ModelError: A section-profile object must produce one complete solid`
- ERROR `test_long_panel_is_one_exact_solid_in_both_orientations` → AC26
  - 訊息：`modeling.common.ModelError: A section-profile object must produce one complete solid`
- ERROR `test_obj_labels_local_reference_material_and_rejects_mixed_frames` → 無對應提案 AC
  - 訊息：`modeling.common.ModelError: A section-profile object must produce one complete solid`
- ERROR `test_parameter_and_fixed_material_sources_survive_native_dump_and_package` → AC14 ~
  - 訊息：`modeling.common.ModelError: A section-profile object must produce one complete solid`
- ERROR `test_spec_update_preview_cancel_confirm_and_invalid_update_preserve_source` → 無對應提案 AC
  - 訊息：`modeling.common.ModelError: A section-profile object must produce one complete solid`
- ERROR `test_tampered_identity_bounds_volume_or_vertices_fail_reconstruction` → 無對應提案 AC
  - 訊息：`modeling.common.ModelError: A section-profile object must produce one complete solid`
- ERROR `test_three_timber_members_and_actual_concave_reference_envelope` → AC08 ~
  - 訊息：`modeling.common.ModelError: A section-profile object must produce one complete solid`
- ERROR `test_uint32_zero_ids_keep_typed_run_member_identity` → 無對應提案 AC
  - 訊息：`modeling.common.ModelError: A section-profile object must produce one complete solid`
- ERROR `test_zero_members_and_unused_profiles_are_preserved` → AC14 ~
  - 訊息：`modeling.common.ModelError: A section-profile object must produce one complete solid`
- FAIL `test_capacity_failures_are_explicit_unsupported_even_with_partial` → 無對應提案 AC
  - 訊息：`AssertionError: 'INVALID' != 'UNSUPPORTED'`

## 提案 AC16 逐條對照

提案 AC16：移除 P-I2、P-I3 或面材寬度上限 → AC04–AC06、AC12、AC21、AC24 分別轉紅；P-R1 `<` 改 `≤` → AC07、AC23 轉紅；`w < 915` 改 `w ≤ 915` → AC21 轉紅。

| 提案要求的突變 | 提案列出的 AC | 實測轉紅的對應 | 未被打紅的 AC |
|---|---|---|---|
| P-I2 移除（SPM01，I44） | AC04、AC05、AC12 | AC04 ← test_all_violations_exact_regions_and_retained_rectangles（相似場景）、test_profile_geometry_and_coordinate_rejections（相似場景）；AC05 ← test_all_violations_exact_regions_and_retained_rectangles（相似場景）、test_concave_not_four_corners_and_winding（相似場景）；AC12 ← test_shrink_reject_and_expand_loses_right_contact（同場景） | 無 |
| P-I3 移除（SPM02，I45） | AC06、AC24 | AC06 ← test_maximum_pair_diagnostics_and_copied_host_capacity_roundtrip（相似場景）、test_touch_edges_points_and_cross_kind_overlap（相似場景）；AC24 ← test_touch_edges_points_and_cross_kind_overlap（相似場景） | 無 |
| 面材寬度上限 `w<915`→`w<=915`（SPM05） | AC21 | AC21 ← test_panel_strict_width_fixed_spec_and_long_run（同場景） | 無 |
| P-R1 u 向 `<`→`<=`（SPM03） | AC07、AC23 | AC07 ← test_touch_edges_points_and_cross_kind_overlap（同場景） | AC23 |
| P-R1 v 向 `<`→`<=`（SPM04） | AC07、AC23 | AC07 ← test_touch_edges_points_and_cross_kind_overlap（同場景） | AC23 |

### 與提案 AC16 的差異（如實）

1. **AC23 沒有被任何突變打紅。** 提案 AC23（面材 w=346 貼在已有的 M1、M2 之間並被接受）在被計入的測試裡不存在：
   唯一把面材 `panel()`（u=27、w=346）貼在角材旁的 `test_source_index_typed_closure_and_display_identity` 被本閘門排除（它要求帶來源／建置收據的 registry binary，拋棄式變異 binary 沒有）；
   modeling 測試沒有 w=346。因此 P-R1 `<`→`<=`（SPM03、SPM04）只由 AC07 的角材貼齊案例（`test_touch_edges_points_and_cross_kind_overlap`）打紅，面材貼齊沒有獨立的紅燈證據。
2. **AC04、AC05、AC06、AC24 是相似場景轉紅，不是提案列的原始數字。** 測試用的座標與輪廓與提案不同（提案 AC04 用 (380,0)、AC05 用 27×27 於 (50,50)、AC06 用 (20,0)、AC24 用 w=346 於 (20,0)；
   測試用的是 u=26 的 1 mm 重疊、面材 w=30 於 u=20、以及凹槽輪廓上的 60×60 與填槽矩形）。條文子句相同、診斷碼相同（`V_PROFILE_OUTSIDE`／`V_PROFILE_OVERLAP`），但不是同一列的逐字場景。
3. **沒有「整個移除面材寬度上限」的獨立案例。** SPM05（`w < 915`→`w <= 915`）是提案 AC16 第三項；第一項裡的「移除面材寬度上限」沒有另立案例，推論上由同一個 w=915 斷言抓到，但這是推論、沒有實測。
4. **AC12、AC21、AC07 與提案同場景轉紅**（390 縮邊、w=915、u=27 貼齊）。
5. 測試方法本身不帶提案 AC 編號，上表是人工對應；一個方法含多個 AC 場景，表裡「含」不等於「該場景是導致轉紅的那一行」。訊息欄（逐案例清單）才是實際失敗的斷言。

