# A/D+B 原 helper 的前 20 個 self／inclusive 條目

來源 `8ab0bdb467ba6e6d22f7c5652f221cffab4934b6`；profile run `20261018T215825197230-gprof`。單位為 gprof 取樣秒，不是 normal 牆鐘耗時或效能倍率。表格逐值保留既有 top20 CSV；同值按名稱排序。cold／model-legacy 原 flat 明示 no time accumulated，零值順位不是有效瓶頸排名。resident 原 flat 累計 0.04 秒，不能把四捨五入成六個 0.01 秒的 self 欄相加成 0.06 秒。inclusive 亦不可跨呼叫層加總。

完整三版本、main/integration 共 840 列見 [CSV](top20-self-inclusive.csv)。

## integration／bridge-cold

| 順位 | self 函式 | self 秒 | inclusive 函式 | inclusive 秒 |
|---:|---|---:|---|---:|
| 1 | `app_asm_context` | 0.00 | `app_asm_context` | 0.00 |
| 2 | `app_assembly_saved_dimensions` | 0.00 | `app_assembly_saved_dimensions` | 0.00 |
| 3 | `app_boundary_compose` | 0.00 | `app_boundary_compose` | 0.00 |
| 4 | `app_boundary_policy` | 0.00 | `app_boundary_policy` | 0.00 |
| 5 | `app_boundary_region_definition` | 0.00 | `app_boundary_region_definition` | 0.00 |
| 6 | `app_boundary_stage` | 0.00 | `app_boundary_stage` | 0.00 |
| 7 | `app_candidate_bind_core` | 0.00 | `app_candidate_bind_core` | 0.00 |
| 8 | `app_candidate_call` | 0.00 | `app_candidate_call` | 0.00 |
| 9 | `app_candidate_check` | 0.00 | `app_candidate_check` | 0.00 |
| 10 | `app_candidate_create_with_deferred_sha` | 0.00 | `app_candidate_create_with_deferred_sha` | 0.00 |
| 11 | `app_candidate_evaluate <cycle 2>` | 0.00 | `app_candidate_evaluate <cycle 2>` | 0.00 |
| 12 | `app_candidate_hash_matches` | 0.00 | `app_candidate_hash_matches` | 0.00 |
| 13 | `app_contact_facts` | 0.00 | `app_contact_facts` | 0.00 |
| 14 | `app_contact_resolve_stops <cycle 1>` | 0.00 | `app_contact_resolve_stops <cycle 1>` | 0.00 |
| 15 | `app_dp_context` | 0.00 | `app_dp_context` | 0.00 |
| 16 | `app_eng_context` | 0.00 | `app_eng_context` | 0.00 |
| 17 | `app_eng_serializable` | 0.00 | `app_eng_serializable` | 0.00 |
| 18 | `app_fs_context` | 0.00 | `app_fs_context` | 0.00 |
| 19 | `app_fs_obstacle_box` | 0.00 | `app_fs_obstacle_box` | 0.00 |
| 20 | `app_grid_context` | 0.00 | `app_grid_context` | 0.00 |

## integration／bridge-resident

| 順位 | self 函式 | self 秒 | inclusive 函式 | inclusive 秒 |
|---:|---|---:|---|---:|
| 1 | `geo_region_is_valid` | 0.01 | `main` | 0.04 |
| 2 | `reference_contact_facts <cycle 1>` | 0.01 | `world_validate_derived` | 0.03 |
| 3 | `reference_guide_clip_text` | 0.01 | `app_scene_candidate_apply` | 0.02 |
| 4 | `wd_write` | 0.01 | `wood_world_validate_members` | 0.02 |
| 5 | `wood_contact_collect_stops` | 0.01 | `app_replace_world.constprop.0` | 0.01 |
| 6 | `wood_eng_version_definition` | 0.01 | `apply_reference_place` | 0.01 |
| 7 | `app_asm_context` | 0.00 | `apply_scene_line <cycle 2>` | 0.01 |
| 8 | `app_assembly_saved_dimensions` | 0.00 | `apply_scene_line_candidate.constprop.0 <cycle 2>` | 0.01 |
| 9 | `app_boundary_compose` | 0.00 | `apply_spec_line` | 0.01 |
| 10 | `app_boundary_policy` | 0.00 | `geo_candidate_evaluate <cycle 2>` | 0.01 |
| 11 | `app_boundary_region_definition` | 0.00 | `geo_region_is_valid` | 0.01 |
| 12 | `app_boundary_stage` | 0.00 | `reference_check_all` | 0.01 |
| 13 | `app_candidate_bind_core` | 0.00 | `reference_checked` | 0.01 |
| 14 | `app_candidate_call` | 0.00 | `reference_contact_facts <cycle 1>` | 0.01 |
| 15 | `app_candidate_check` | 0.00 | `reference_guide_clip_text` | 0.01 |
| 16 | `app_candidate_create_with_deferred_sha` | 0.00 | `reference_member_footprint` | 0.01 |
| 17 | `app_candidate_evaluate <cycle 2>` | 0.00 | `reference_preview_text` | 0.01 |
| 18 | `app_candidate_hash_matches` | 0.00 | `wd_evaluate <cycle 1>` | 0.01 |
| 19 | `app_contact_facts` | 0.00 | `wd_write` | 0.01 |
| 20 | `app_contact_resolve_stops <cycle 1>` | 0.00 | `wood_contact_collect_stops` | 0.01 |

## integration／model-legacy

| 順位 | self 函式 | self 秒 | inclusive 函式 | inclusive 秒 |
|---:|---|---:|---|---:|
| 1 | `app_asm_context` | 0.00 | `app_asm_context` | 0.00 |
| 2 | `app_assembly_saved_dimensions` | 0.00 | `app_assembly_saved_dimensions` | 0.00 |
| 3 | `app_boundary_compose` | 0.00 | `app_boundary_compose` | 0.00 |
| 4 | `app_boundary_policy` | 0.00 | `app_boundary_policy` | 0.00 |
| 5 | `app_boundary_region_definition` | 0.00 | `app_boundary_region_definition` | 0.00 |
| 6 | `app_boundary_stage` | 0.00 | `app_boundary_stage` | 0.00 |
| 7 | `app_candidate_bind_core` | 0.00 | `app_candidate_bind_core` | 0.00 |
| 8 | `app_candidate_call` | 0.00 | `app_candidate_call` | 0.00 |
| 9 | `app_candidate_check` | 0.00 | `app_candidate_check` | 0.00 |
| 10 | `app_candidate_create_with_deferred_sha` | 0.00 | `app_candidate_create_with_deferred_sha` | 0.00 |
| 11 | `app_candidate_evaluate <cycle 2>` | 0.00 | `app_candidate_evaluate <cycle 2>` | 0.00 |
| 12 | `app_candidate_hash_matches` | 0.00 | `app_candidate_hash_matches` | 0.00 |
| 13 | `app_contact_facts` | 0.00 | `app_contact_facts` | 0.00 |
| 14 | `app_contact_resolve_stops <cycle 1>` | 0.00 | `app_contact_resolve_stops <cycle 1>` | 0.00 |
| 15 | `app_dp_context` | 0.00 | `app_dp_context` | 0.00 |
| 16 | `app_eng_context` | 0.00 | `app_eng_context` | 0.00 |
| 17 | `app_eng_serializable` | 0.00 | `app_eng_serializable` | 0.00 |
| 18 | `app_fs_context` | 0.00 | `app_fs_context` | 0.00 |
| 19 | `app_fs_obstacle_box` | 0.00 | `app_fs_obstacle_box` | 0.00 |
| 20 | `app_grid_context` | 0.00 | `app_grid_context` | 0.00 |

## integration／model-neutral

| 順位 | self 函式 | self 秒 | inclusive 函式 | inclusive 秒 |
|---:|---|---:|---|---:|
| 1 | `_init` | 0.01 | `_init` | 0.01 |
| 2 | `app_asm_context` | 0.00 | `app_asm_context` | 0.00 |
| 3 | `app_assembly_saved_dimensions` | 0.00 | `app_assembly_saved_dimensions` | 0.00 |
| 4 | `app_boundary_compose` | 0.00 | `app_boundary_compose` | 0.00 |
| 5 | `app_boundary_policy` | 0.00 | `app_boundary_policy` | 0.00 |
| 6 | `app_boundary_region_definition` | 0.00 | `app_boundary_region_definition` | 0.00 |
| 7 | `app_boundary_stage` | 0.00 | `app_boundary_stage` | 0.00 |
| 8 | `app_candidate_bind_core` | 0.00 | `app_candidate_bind_core` | 0.00 |
| 9 | `app_candidate_call` | 0.00 | `app_candidate_call` | 0.00 |
| 10 | `app_candidate_check` | 0.00 | `app_candidate_check` | 0.00 |
| 11 | `app_candidate_create_with_deferred_sha` | 0.00 | `app_candidate_create_with_deferred_sha` | 0.00 |
| 12 | `app_candidate_evaluate <cycle 2>` | 0.00 | `app_candidate_evaluate <cycle 2>` | 0.00 |
| 13 | `app_candidate_hash_matches` | 0.00 | `app_candidate_hash_matches` | 0.00 |
| 14 | `app_contact_facts` | 0.00 | `app_contact_facts` | 0.00 |
| 15 | `app_contact_resolve_stops <cycle 1>` | 0.00 | `app_contact_resolve_stops <cycle 1>` | 0.00 |
| 16 | `app_dp_context` | 0.00 | `app_dp_context` | 0.00 |
| 17 | `app_eng_context` | 0.00 | `app_eng_context` | 0.00 |
| 18 | `app_eng_serializable` | 0.00 | `app_eng_serializable` | 0.00 |
| 19 | `app_fs_context` | 0.00 | `app_fs_context` | 0.00 |
| 20 | `app_fs_obstacle_box` | 0.00 | `app_fs_obstacle_box` | 0.00 |
