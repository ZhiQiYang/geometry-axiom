#!/usr/bin/env python3
"""One entry point for every non-browser test; reports pass/fail/skip and environment problems honestly.

    python tests/run_all.py                 # check binaries; stale/missing ones are NOT used and their suites are not run
    python tests/run_all.py --build         # build stale/missing binaries first (tests/binaries.py), then run
    python tests/run_all.py --only bridge   # only suites whose name contains "bridge"  (repeatable)   [PARTIAL run]
    python tests/run_all.py --list          # show the suites and what each needs
    python tests/run_all.py --allow-skip    # skips no longer affect the exit code
    python tests/run_all.py --simulate-missing GEOMETRY_MODEL_BASE   # run as if that variable were unset [DEMO run, never exit 0]
    python tests/run_all.py --update-expected   # full run only: rewrite tests/run_all.expected.json from what was discovered

Exit codes (lowest number wins): 1 any test failed / suite crashed / timed out / discovered count differs from
run_all.expected.json / unregistered test file; 2 environment problem (stale or missing binary, SAC block, node missing,
canvas shim did not redirect, run_tests exit 2, another run_all or build is running); 3 only skips (unless --allow-skip);
4 a --simulate-missing demo that would otherwise have been 0; 0 everything that was selected passed.
A complete run (no --only / --extra-py / --simulate-missing) that exits 0 means: every suite ran, every suite found exactly
the number of tests listed in tests/run_all.expected.json, none failed, none was skipped (the only exemption is the named
allowlist ALLOWED_SKIPS, e.g. the POSIX-only /dev/full test on Windows).  Partial/demo runs say so in their last lines.

NOT covered: required production-owner integration and real-browser gates in
tests/INTEGRATION-GATES.md; run them separately before claiming product completion.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import unicodedata

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import binaries  # noqa: E402

IS_WIN = os.name == 'nt'
LOG_DIR = binaries.OUT_DIR / 'run_all-logs'
RUNNER = HERE / '_unittest_runner.py'
EXPECTED_FILE = HERE / 'run_all.expected.json'

# ---------------------------------------------------------------- registries
# Every tests/test_*.py MUST appear here (value = native binaries it needs; [] is a deliberate "needs none").
# A test file that is on disk but not listed makes run_all fail and name it.
PY_NEEDS = {
    'test_geo318_reading_a_oracle': [],
    'test_geo318_reading_a_native': [],
    'test_geo314_stagger_commit': ['bridge'],
    'test_geo314_commit_paths': [],
    'test_geo314_ordered_facts': [],
    'test_architecture_contract': [],
    'test_product_architecture': [],
    'test_assembly_capacity': ['bridge'],
    'test_assembly_candidate_impact': ['bridge'],
    'test_assembly_parameter_refs': ['bridge'],
    'test_assembly_native_diagnostics': ['bridge'],
    'test_assembly_mutation_check': [],
    'test_assembly_rules': ['bridge'],
    'test_section_profile_native': ['bridge', 'model-base'],
    'test_panel_fill_finish_surface': ['bridge'],
    'test_panel_fill_layout': ['bridge'],
    'test_panel_fill_host': ['bridge'],
    'test_panel_fill_support': ['bridge', 'pf3-algorithm'],
    'test_section_profile_modeling': ['bridge', 'model-base'],
    'test_section_profile_mutation_check': [],
    'test_assembly_generation': ['bridge'],
    'test_axiom_reader': [],
    'test_binaries': [],
    'test_bridge_integrity': ['bridge'],
    'test_cli_args': ['core'],
    'test_datum_contract': ['bridge'],
    'test_domain_decoupling_proposal': [],
    'test_domain_decoupling_adoption': [],
    'test_domain_decoupling_compatibility': ['model-base'],
    'test_engineering_core': ['bridge'],
    'test_engineering_json': ['engjson'],
    'test_engineering_model_compatibility': ['model-base'],
    'test_engineering_model_sources': ['bridge', 'model-base'],
    'test_engineering_transport': [],
    'test_evidence_link_native': ['bridge'],
    'test_feedback_store': [],
    'test_gdi_contract': ['gdi'],
    # These suites build isolated K objects and their actual product witness;
    # no prebuilt repository binary is accepted as a substitute.
    'test_geo261_native_kernel': [],
    'test_geo261_native_geometry': [],
    'test_geo261_native_grid': [],
    'test_domain_source_pins': [],
    'test_source_closure_memo': [],
    'test_mutation_anchors': [],
    'test_geometry_host_native': [],
    'test_geometry_host_sources': [],
    'test_geometry_source_runtime': [],
    'test_rectangular_python': [],
    'test_rectangular_bridge': [],
    'test_geometry_host_world': [],
    'test_geometry_kernel_compatibility': [],
    'test_geometry_kernel_geometry': [],
    'test_geometry_kernel_graph': [],
    'test_geometry_kernel_isolation': [],
    'test_geo261_native_parameters': [],
    'test_geo261_draw_annotation': [],
    'test_geo261_native_linear': [],
    'test_geo261_region_edges': [],  # Builds isolated K and its own same-source bridge.
    'test_geo261_native_datums': [],
    'test_geometry_kernel_runtime': [],
    'test_geometry_kernel_session': [],
    'test_geometry_kernel_transactions': [],
    'test_geo261_native_sources': [],
    'test_geo261_wood_members': [],
    'test_geo261_wood_product': [],
    'test_geo261_native_entrypoints': [],
    'test_geo261_model_sources': [],
    'test_geo261_default_native': ['bridge', 'model-base'],
    'test_geo261_wood_supports': [],
    'test_geo261_wood_supports_product': [],
    'test_geo261_native_regions': [],
    'test_geo261_regions_product': [],
    'test_geo261_wood_contacts': [],
    'test_geo261_wood_contacts_product': [],
    'test_geo261_native_grid_store': [],
    'test_geo261_host_history': [],
    'test_geo261_native_guides': [],
    'test_geo261_native_candidate': [],
    'test_geo261_host_candidate': [],
    'test_geo261_native_placements': [],
    'test_geo261_domain_product': [],
    'test_geo261_candidate_product': [],
    'test_geo261_staged_candidate_graph': [],
    'test_geo261_native_grid_product': [],
    'test_geo261_wood_engineering': [],
    'test_geo261_wood_assembly': [],
    'test_geo261_wood_section_profile': [],
    'test_geo261_guides_product': [],
    'test_geo261_panel_native': [],
    'test_geo261_assembly_graph_product': [],
    'test_geo261_assembly_sources': [],
    'test_geo261_candidate_cache': [],
    'test_geo261_candidate_deferred_sha': [],
    'test_geo261_deferred_candidate': [],
    'test_geo261_deferred_product': [],
    'test_geo261_contact_sources': [],
    'test_geo261_engineering_sources': [],
    'test_geo261_definition_sources': [],
    'test_geo261_definition_graph_product': [],
    'test_geo261_derived_policy_sources': [],
    'test_geo261_derived_policy_graph_product': [],
    'test_geo261_enclosure_sources': [],
    'test_geo261_enclosure_product': [],
    'test_geo261_finish_sources': [],
    'test_geo261_graph_product': [],
    'test_geo261_grid_sources': [],
    'test_geo261_grid_definitions_product': [],
    'test_geo261_region_key_sources': [],
    'test_geo261_member_reference': [],
    'test_geo261_mutation_migration': [],
    'test_geo261_native_document': [],
    'test_geo261_native_enclosures': [],
    'test_geo261_native_grid_rules': [],
    'test_geo261_native_versions': [],
    'test_geo261_parameter_sources': [],
    'test_geo261_parameter_definition_sources': [],
    'test_geo261_linear_definition_sources': [],
    'test_geo261_linear_definition_graph_product': [],
    'test_geo261_version_field_sources': [],
    'test_geo261_host_authority': [],
    'test_geo261_engineering_parameter_authority': [],
    'test_geo261_assembly_definition_authority': [],
    'test_geo261_finish_definition_authority': [],
    'test_geo261_grid_definition_codec': [],
    'test_geo261_grid_definition_authority': [],
    'test_geo261_source_context': [],
    'test_geo261_enclosure_definition_authority': [],
    'test_geo261_model_vertex_ledger': [],
    'test_geo261_model_base_replay': [],
    'test_geo261_host_placement_definition': [],
    'test_geo261_application_closure': [],
    'test_geo261_placement_definition': [],
    'test_geo261_model_semantics_authority': [],
    'test_geo261_host_facts_authority': [],
    'test_geo261_placement_sources': [],
    'test_geo261_section_profile_sources': [],
    'test_geo261_section_profile_authority': [],
    'test_geo261_source_describe': [],
    'test_geo261_source_index': [],
    'test_geo261_load_residual': [],
    'test_geo261_version_activation': [],
    'test_geo261_wood_contact_world': [],
    'test_geo261_wood_derived_placement': [],
    'test_geo261_wood_engineering_operations': [],
    'test_geo261_wood_finish': [],
    'test_geo261_wood_grid_application': [],
    'test_geo261_wood_grid_cells': [],
    'test_geo261_wood_grid_engineering': [],
    'test_geo261_wood_member_declaration': [],
    'test_geo261_wood_report_policy': [],
    'test_geo261_timber_capacity': [],
    'test_geo261_timber_capacity_host': [],
    'test_geo300_validation_memo': [],
    'test_geo300_contact_result_memo': [],
    'test_geo300_contact_order_fast': [],
    'test_geo300_source_node_slot': [],
    'test_geo300_source_edge_scope': [],
    'test_geo300_dead_contact_facts': [],
    'test_geo300_source_node_hint': [],
    'test_geo261_wood_world_validation': [],
    'test_grid_system_contract': ['bridge'],
    'test_grid_card_reference': ['bridge', 'model-base'],
    'test_grid_inspector_contract': ['bridge'],
    'test_grid_subdivision_oracle': ['bridge'],
    'test_grid_trial_contract': ['bridge'],
    'test_guide_panels': [],
    'test_infinite_grid_contract': ['bridge'],
    'test_modeling_degenerate': ['model-base'],
    'test_modeling_runtime': ['model-base'],
    'test_modeling_transport': ['bridge', 'model-base'],
    'test_model_update': ['bridge', 'model-base'],
    'test_mutation_freshness': [],
    'test_parameters_core': ['bridge', 'model-base'],
    'test_parameter_retirement_scope': ['bridge'],
    'test_parameter_netzero': ['bridge'],
    'test_parameters_final_candidate': ['bridge'],
    'test_parameters_unbind_scope': ['bridge'],
    'test_parameters_deleted_unbind': ['bridge'],
    'test_parameters_upstream_unbind': ['bridge'],
    'test_parameters_candidate_value_history': ['bridge'],
    'test_reference_contract': ['bridge'],
    'test_rectangular_template': [],
    'test_recorded_api_receipts': [],
    'test_release_gate': [],
    'test_local_launcher': ['core', 'bridge', 'model-base'],
    'test_rule_case_workbench_http': ['bridge'],
    'test_rule_case_host': ['bridge'],
    'test_rule_case_catalog': ['bridge'],
    'test_rule_case_definition': [],
    'test_rule_case_executor': ['bridge'],
    'test_rule_case_request': ['bridge'],
    'test_source_inspector': ['bridge'],
    'test_source_inspector_transport': [],
    'test_runtime_version': [],
    'test_scenario_verify': ['bridge', 'model-base'],
    'test_scene_import': ['bridge'],
    'test_serve': [],
    'test_wait_trace': [],
    'test_space_modeling': ['model-base'],
    'test_subgrid_contract': ['bridge'],
    'test_timber_support_projection': [],
    'test_unittest_runner': [],
    'test_witness_diagnostics': [],
    'test_witness_marks': [],
}
# Every tests/*.js|*.cjs|*.mjs MUST be in exactly one of these three (run by `node --test`, run as a script, or a
# reasoned exclusion).  Unlisted files make run_all fail and name them.
PY_BROWSER_GATES = {
    'test_issue123_create_feedback_browser': 'Explicit isolated Playwright mouse/touch first-center gate from #131; run with --url/--out, not a unittest suite',
}
NODE_TEST_FILES = [
    'tests/test_grid_inspector_stagger.cjs',
    'tests/test_transport_failure_trace.js',
    'tests/test_section_profile_compat.js',
    'tests/test_assembly_project_store.js',
    'tests/test_assembly_transport_context.js',
    'tests/test_assembly_workspace.js',
    'tests/test_cdp_floor.js',
    'tests/test_engineering_project_store.js',
    'tests/test_face_projection_store.js',
    'tests/test_grid_trial_geometry.js',
    'tests/test_grid_rule_draft.js',
    'tests/test_grid_drafts_collection.js',
    'tests/test_grid_drafts_lifecycle_capacity.js',
    'tests/test_grid_rule_lines.js',
    'tests/test_issue77_attachment.js',
    'tests/test_issue77_history.js',
    'tests/test_issue77_workspace.js',
    'tests/test_k4_evidence.js',
    'tests/test_model_snapshot_schedule.js',
    'tests/test_model_snapshot_navigation.js',
    'tests/test_model_update.js',
    'tests/test_parameters_project_store.js',
    'tests/test_card_reference_project_store.js',
    'tests/test_project_store.js',
    'tests/test_shared_format17.js',
    'tests/test_subdivision_project_store.js',
    'tests/test_reference_workspace_races.js',
    'tests/test_room_outline.js',
    'tests/test_room_multi_candidate.js',
    'tests/test_room_collection.js',
    'tests/test_scenario_diff.js',
    'tests/test_scenario_review_native.js',
    'tests/test_scenario_snapshots.js',
    'tests/test_scenario_project_store.js',
    'tests/test_scenario_editor_tickets.js',
    'tests/test_scenario_recovery_owner.js',
    'tests/test_scenario_resume_checkpoint.js',
    'tests/test_shared_room_display.js',
    'tests/test_rule_case_project_store.js',
    'tests/test_source_inspector.js',
    'tests/test_space_model_store.js',
    'tests/test_timber_schedule.js',
    'tests/test_timber_supports.js',
]
NODE_SCRIPT_FILE = 'tests/test_model_viewer.cjs'
NODE_DOCUMENT_SCRIPT_FILES = {
    'node:document_format': 'tests/test_document_format.js',
    'node:document_cases': 'tests/test_document_cases.js',
    'node:cdp_navigation': 'tests/test_cdp_navigation.js',
    'node:cdp_confirmation_gate': 'tests/test_cdp_confirmation_gate.js',
}
NODE_PURE_TEST_FILES = {
    'node:draw_annotation': 'tests/test_draw_annotation.js',
    'node:woodworking_frontend': 'tests/test_woodworking_frontend.js',
    'node:grid_inspector_command': 'tests/test_grid_inspector_command.js',
    'node:grid_lesson_control_ownership': 'tests/test_grid_lesson_control_ownership.js',
    'node:parameter_confirmation_settlement': 'tests/test_parameter_confirmation_settlement.js',
    'node:face_reference_settlement': 'tests/test_face_reference_settlement.js',
    'node:face_projection_lifecycle': 'tests/test_face_projection_lifecycle.js',
    'node:workspace_shell_history': 'tests/test_workspace_shell_history.js',
    'node:feedback_events': 'tests/test_feedback_events.js',
    'node:space_test_floor': 'tests/test_space_test_floor.js',
    'node:history_operation': 'tests/test_history_operation.js',
    'node:context_operations': 'tests/test_context_operations.js',
    'node:cdp_evaluation': 'tests/test_cdp_evaluation.js',
    'node:cdp_settle': 'tests/test_cdp_settle.js',
    'node:cdp_card_position': 'tests/test_cdp_card_position.js',
    'node:background_grid_viewport': 'tests/test_background_grid_viewport.js',
    'node:anchor_band_clip': 'tests/test_anchor_band_clip.js',
    'node:hover_pick_scheduler': 'tests/test_hover_pick_scheduler.js',
    'node:face_paint_scheduler': 'tests/test_face_paint_scheduler.js',
    'node:room_outline_worker': 'tests/test_room_outline_worker.js',
    'node:room_outline_closeout': 'tests/test_room_outline_closeout.js',
    'node:evidence_links': 'tests/test_evidence_links.js',
    'node:evidence_project_store': 'tests/test_evidence_project_store.js',
    'node:grid_definition_diagram': 'tests/test_grid_definition_diagram.js',
}
NODE_EXCLUDED = {
    'tests/k1b_cutting_settings_fixture.cjs': 'Pinned K1-b validator fixture for the shared /17 owner-dispatch contract; not an executable test',
    'tests/k2a_browser_receipt.cjs': 'Shared browser receipt/identity helper; registers no tests',
    'tests/k2a_rule_repin_browser.cjs': 'Required actual source-rule raw preservation and two-way repin comparison gate',
    'tests/k2a_source_repin_browser.cjs': 'Required isolated K2a-A Chromium source repin/replacement gate: stale cancellation, same-ID lost refusal and reviewed different-ID selection',
    'tests/k2a_zip_browser.cjs': 'Required K2a-A true ZIP save/import into another fresh isolated service; set GEOMETRY_FRESH_TEST_URL as well as GEOMETRY_TEST_URL',
    'tests/k2a_native_browser.cjs': 'Required isolated K2a-A native confirm/Undo, deletion receipts, permanent orphans/lost and same-ID recreation through the actual browser owner',
    'tests/k2a_drafts_browser.cjs': 'Required isolated K2a-A real Chromium 1280/390 draft collection/continuation gate; run with GEOMETRY_ISOLATED_SERVICE=1 and GEOMETRY_TEST_URL',
    'tests/room_multi_candidate_browser.js': 'Required isolated same-page candidate sessions through actual room owner, Worker/source invalidation, interrupted replies, history and fresh-context ZIP reopen',
    'tests/test_section_profile_browser.js': 'Required isolated Q38 native/UI model, desktop/390, keyboard, preview/cancel, placement and real project Save/new/Open gate; run separately, not a node unit suite',
    'tests/rule-case-workbench-controller.cjs': 'Required actual standalone HTTP/native controller lifecycle suite; needs explicit isolated GEOMETRY_RULE_CASE_TEST_URL; not a generic node fixture',
    'tests/rule-case-workbench-browser.cjs': 'Required real standalone component browser gate at 1280/390 over native HTTP; formal ZIP flow is separate',
    'tests/test_rule_case_app_races.js': 'Required formal original GET/create/retention/history/native/B-context races and live assembly candidate preservation; explicit isolated service/TEMP fixtures; see INTEGRATION-GATES.md',
    'tests/test_rule_case_app_browser.js': 'Required formal app/native six cases, races, metadata Undo/Redo, A/B closure and ZIP Save/blank-context reopen at 1280/390; see INTEGRATION-GATES.md',

    'tests/test_shared_room_display_browser.js': 'Required isolated shared-room view adoption, per-room dirty/history/basis, true Undo/Redo and real ZIP Save/new-context Open at 1280/390; see INTEGRATION-GATES.md',
    'tests/test_scenario_workflow_browser.js': 'Required isolated formal A/B editing, compare/adopt, undo/redo, real ZIP Save/new-context reopen at 1280/390px; see INTEGRATION-GATES.md',
    'tests/test_scenario_lifecycle_browser.js': 'Required isolated formal scenario/native lifecycle gate: held Cancel/Capture/confirm, unknown terminal recovery, lost create/close; see INTEGRATION-GATES.md',
    'tests/room_outline_keyboard_browser.js': 'Required isolated real keyboard/click-equivalence gate with formal PDF import/calibration and exact candidate/native checks; composition and stale DOM delivery are explicit fault injection; see INTEGRATION-GATES.md',
    'tests/room_outline_acceptance_browser.js': 'Required isolated formal app/native PDF-image UI, actual Save/new-context Open and model continuation; installed Playwright/Chromium and dedicated service, default full scenarios; see INTEGRATION-GATES.md',
    'tests/room_outline_pan_browser.js': 'Required isolated real keyboard/mouse pan and cancellation gate with native dump preservation; API-authored initial fixture and explicit pointercancel injection; see INTEGRATION-GATES.md',
    'tests/room_outline_worker_browser.js': 'Required isolated native Worker computation and UI invalidation gate; API-authored setup and explicit late-consumer delivery injection; see INTEGRATION-GATES.md',
    'tests/test_grid_rule_reader_browser.js': 'Required isolated /13 formal reader UI/native gate: canonical candidate, evidence snapshot, zero-confirm rejection and actual ZIP Save; see INTEGRATION-GATES.md',
    'tests/test_issue116_browser.js': 'Required isolated native/browser B-menu gate, full Save/reopen and visual evidence; see INTEGRATION-GATES.md',
    'tests/test_issue116_canvases_browser.js': 'Required isolated K4 gate: face-menu characterization + ContextMenuShell contract (PR-a); cursor/object-canvas/touch segments follow in PR-b/c/d; see INTEGRATION-GATES.md',
    'tests/scenario_browser_check.cjs': 'Required isolated scenario-module Chromium/ZIP harness; fresh receipt-backed native adapters and Playwright; run separately (INTEGRATION-GATES.md)',
    'tests/test_scenario_grid_interface.js': 'Required real GridDraft owner-validator compatibility; PR104 is not on main; execute with actual owner validator, never count missing-injection skip as pass (INTEGRATION-GATES.md)',
    'tests/issue77_attachment_fixture.js': 'Shared self-authored PDF/payload fixture; registers no tests',
    'tests/test_issue77_browser.js': 'Required real app/native/Chromium room acceptance; formal owner exists, execute separately; see INTEGRATION-GATES.md',
    'tests/test_issue77_exit_browser.js': 'Required real app/native/Chromium room draft-exit gate; formal owner exists, execute separately; see INTEGRATION-GATES.md',
    'tests/test_issue77_recovery_browser.js': 'Required real app/native/Chromium room recovery gate; formal owner exists, execute separately; see INTEGRATION-GATES.md',
    'tests/test_issue77_remove_browser.js': 'Required real app/native/Chromium room unlink/removal gate; formal owner exists, execute separately; see INTEGRATION-GATES.md',
    'tests/room_outline_fixture.js': 'Self-authored PDF/scan fixture generator; not a node test',
    'tests/reference_pdf_fixture.js': '夾具產生器，不是測試：node --test 會把它算成 1 個假的通過 test',
    'tests/browser_race_ownership_instrumentation.js': 'Supplemental observer injected by tests/browser_race_ownership.py; registers no tests and is not a node suite',
    'tests/issue123_adopted_slices_browser.cjs': 'Standalone Playwright probe; needs GEOMETRY_ISOLATED_SERVICE=1, a dedicated localhost GEOMETRY_TEST_URL and full GEOMETRY_EXPECTED_SHA. Not a CI suite; see INTEGRATION-GATES.md',
    'tests/issue123_caption_browser.cjs': 'Standalone Playwright caption probe; same isolated service, URL and SHA requirements as the adopted-slices probe. Not a CI suite; see INTEGRATION-GATES.md',
    'tests/room_outline_direct_rows_browser.js': 'Standalone Playwright direct-row harness; needs GEOMETRY_TEST_URL on an isolated service. Not a CI suite; see INTEGRATION-GATES.md',
}
REQUIRED_OWNER_GATES = {
    'tests/integration/issue77_attachment_owner.js': 5,
}
# Runtime adapter checks, separate from non-browser source suites and formal owner completion.
REQUIRED_BROWSER_GATES = {
    'tests/k2a_drafts_browser.cjs': 27,
    'tests/k2a_native_browser.cjs': 42,
    'tests/k2a_source_repin_browser.cjs': 14,
    'tests/k2a_zip_browser.cjs': 89,
    'tests/k2a_rule_repin_browser.cjs': 35,
    'tests/room_multi_candidate_browser.js': 34,
    'tests/test_section_profile_browser.js': 68,
    'tests/integration/q38_save_roundtrip.py': 18,
    'tests/integration/model_library_history_browser.py': 35,
    'tests/integration/save_roundtrip_acceptance.cjs': 33,
    'tests/rule-case-workbench-browser.cjs': 91,
    'tests/test_rule_case_app_browser.js': 76,
    'tests/test_rule_case_app_races.js': 30,
    'tests/room_outline_keyboard_browser.js': 396,
    'tests/room_outline_acceptance_browser.js': 253,
    'tests/room_outline_pan_browser.js': 32,
    'tests/room_outline_worker_browser.js': 78,
    'geometry-web/feedback_resize_observer_test.js': 38,
    'tests/test_grid_rule_reader_browser.js': 34,
    'geometry-web/evidence_links_browser_check.js': 67,
    'geometry-web/evidence_links_integration_test.js': 110,
    'geometry-web/grid_raw_provenance_browser_test.py': 207,
}
BROWSER_GATE_SCOPES = {
    'tests/k2a_drafts_browser.cjs': 'real 1280/390 collection continuation, source repin/cancel and lost save',
    'tests/k2a_native_browser.cjs': 'actual native confirmation/deletion receipts, history and permanent lost browser owner',
    'tests/k2a_source_repin_browser.cjs': 'explicit binding source selection, stale cancel and permanent same-ID lost rejection',
    'tests/k2a_zip_browser.cjs': 'true ZIP and cold isolated native reopen including permanent lost; distinct service sessions required',
    'tests/k2a_rule_repin_browser.cjs': 'actual D19a rule changed/deleted repin with valid/invalid raw, cancellation and close preservation',
    'tests/room_multi_candidate_browser.js': 'real same-page multiroom import/calibration/select/review/accept/park/save/new/Open; explicit late Worker and lost-response injections',
    'tests/test_section_profile_browser.js': 'real desktop/390 Q38 authoring, typed sources, exact models, source impact/cancel, placement conversion, shared history and /16 Save/Open',
    'tests/integration/q38_save_roundtrip.py': 'native-authored complete section fixture; real download/fresh-browser chooser, full World and exact mesh oracle; explicit download fallback, not OS picker',
    'tests/integration/model_library_history_browser.py': 'real model-library/native Undo, Web Locks, drafts and explicit late-owner injections',
    'tests/integration/save_roundtrip_acceptance.cjs': 'real form/native/model/download/file-chooser roundtrip and explicit save-failure injection',
    'tests/rule-case-workbench-browser.cjs': 'standalone component/native',
    'tests/test_rule_case_app_browser.js': 'formal app/native/ZIP/history',
    'tests/test_rule_case_app_races.js': 'formal app/native/context races',
    'tests/test_grid_rule_reader_browser.js': 'formal app/native/grid/ZIP',
    'geometry-web/evidence_links_browser_check.js': 'independent injected-backend adapter',
    'geometry-web/evidence_links_integration_test.js': 'formal app/PDF/ZIP/history',
    'geometry-web/grid_raw_provenance_browser_test.py': 'formal raw enum/pin provenance, ZIP cold reopen, explicit correction and native Undo/Redo',
}

BROWSER_GATE_SCOPES.update({
    'tests/room_outline_keyboard_browser.js': 'real keyboard/click parity; synthetic composition and stale DOM guards',
    'tests/room_outline_acceptance_browser.js': 'formal room app/PDF-image/UI/ZIP/model',
    'tests/room_outline_pan_browser.js': 'real input/native preservation; API fixture and injected pointercancel',
    'tests/room_outline_worker_browser.js': 'native Worker/UI invalidation with injected late-consumer delivery',
})

BROWSER_GATE_SCOPES.update({
    'geometry-web/feedback_resize_observer_test.js': 'real ResizeObserver/error/manual-report events; owned fresh/root/source/runtime identity required',
})

# Platform-inherent skips: exempt only when suite + exact test id + reason substring + platform ALL match.
# Any other skip (even one whose reason mentions POSIX) stays a skip.
ALLOWED_SKIPS = [
    {'suite': 'py:test_gdi_contract',
     'test': 'test_gdi_contract.GdiContract.test_confirmed_failures_release_real_resources',
     'reason': 'requires compiled Windows GDI contract harness',
     'platforms': ('posix',),
     'why': 'Windows GDI resources do not exist on POSIX; all native geometry suites still run'},
    {'suite': 'py:test_cli_args',
     'test': 'test_cli_args.CliArgs.test_svg_write_failure_is_reported_without_unlinking_device',
     'reason': 'requires POSIX full device',
     'platforms': ('nt',),
     'why': '/dev/full 是 POSIX 裝置，Windows 上不存在'},
    {'suite': 'py:test_assembly_mutation_check',
     'test': 'test_assembly_mutation_check.AssemblyMutationCheck.test_run_logged_kills_the_whole_group_and_records_that_nothing_is_left',
     'reason': 'requires POSIX process groups and /proc',
     'platforms': ('nt',),
     'why': '程序群組與 /proc 是 POSIX／Linux 才有的東西，Windows 上不存在；Linux／WSL／CI 照常真的執行'},
]
SAC_FACES = ['橋接器連線中斷', 'WinError 4551', 'BASE_COMPILER', 'UNSUPPORTED', '應用程式控制原則', 'Smart App Control']
UNIT = {'integrity': 'C 檢查點', 'run_tests': '場景', 'unittest': 'test', 'node-test': 'node test', 'node-canvas': '斷言'}


class Suite:
    def __init__(self, name, kind, cmd, needs=(), timeout=900, needs_node=False, extra_env=None, label=''):
        self.name = name
        self.kind = kind
        self.cmd = cmd
        self.needs = list(needs)
        self.timeout = timeout
        self.needs_node = needs_node
        self.extra_env = extra_env or {}
        self.label = label

    @property
    def counted(self):
        return self.kind not in ('node-script', 'python-script', 'mutation-check')


class Row:
    def __init__(self, suite_name, counted=True):
        self.name = suite_name
        self.counted = counted
        self.total = self.passed = self.failed = self.skipped = 0
        self.seconds = 0.0
        self.note = ''
        self.ran = False
        self.allowed_skips = 0      # skips matched by the named ALLOWED_SKIPS list: shown, but not an exit-3 reason
        self.env_problem = False    # counts towards exit code 2
        self.crashed = False        # counts towards exit code 1 even without a failed test
        self.expected_problem = ''  # discovered count differs from run_all.expected.json
        self.details = []


def node_exe():
    return shutil.which('node')


# ------------------------------------------------------------------ registry checks

def check_registry():
    """Problems (list of str) between what is on disk under tests/ and what this file registers."""
    problems = []
    disk_py = {p.stem for p in HERE.glob('test_*.py')}
    for stem in sorted(disk_py - set(PY_NEEDS) - set(PY_BROWSER_GATES)):
        problems.append('tests/%s.py 沒有登記在 run_all.py 的 PY_NEEDS（沒有二進位需求也要明確登記成 []）；未登記的檔不會被跑' % stem)
    for stem in sorted((set(PY_NEEDS) | set(PY_BROWSER_GATES)) - disk_py):
        problems.append('PY_NEEDS 登記了 %s，但 tests/%s.py 不存在' % (stem, stem))
    disk_js = {'tests/' + p.name for pattern in ('*.js', '*.cjs', '*.mjs') for p in HERE.glob(pattern)}
    known = (set(NODE_TEST_FILES) | {NODE_SCRIPT_FILE} | set(NODE_DOCUMENT_SCRIPT_FILES.values()) |
             set(NODE_PURE_TEST_FILES.values()) | set(NODE_EXCLUDED))
    for rel in sorted(disk_js - known):
        problems.append('%s 沒有登記在 run_all.py（NODE_TEST_FILES／NODE_SCRIPT_FILE／NODE_DOCUMENT_SCRIPT_FILES／NODE_PURE_TEST_FILES／NODE_EXCLUDED）；未登記的檔不會被跑' % rel)
    for rel in sorted(known - disk_js):
        problems.append('run_all.py 登記了 %s，但該檔不存在' % rel)
    for rel in REQUIRED_OWNER_GATES:
        if not (ROOT / rel).is_file():
            problems.append('必要正式整合驗證入口不存在：%s' % rel)
    for rel in REQUIRED_BROWSER_GATES:
        if not (ROOT / rel).is_file():
            problems.append('必要獨立瀏覽器驗證入口不存在：%s' % rel)
    return problems


def build_suites():
    py = sys.executable
    suites = [
        Suite('c:integrity', 'integrity', None, ['integrity'], 300, label='tests/test_core_integrity.c'),
        Suite('core:run_tests', 'run_tests', None, ['core'], 900, label='tests/run_tests.py <core>'),
        Suite('mutation:check', 'mutation-check', [py, str(HERE / 'mutate.py'), '--check'], [], 120,
              label='tests/mutate.py --check (saved current-source mutation receipts)'),
        Suite('oracle:framing-selftest', 'python-script',
              [py, str(ROOT / 'geometry-core/framing-template/oracle/selftest.py')], [], 900,
              label='geometry-core/framing-template/oracle/selftest.py (mutants + golden + geometry sweep)'),
    ]
    for stem in sorted(PY_NEEDS):
        f = HERE / (stem + '.py')
        if f.is_file():
            suites.append(Suite('py:' + stem, 'unittest', [py, str(RUNNER), str(f)], PY_NEEDS[stem], 1200,
                                needs_node=(stem == 'test_evidence_link_native'), label='tests/%s' % f.name))
    js = [rel for rel in sorted(NODE_TEST_FILES) if (ROOT / rel).is_file()]
    suites += [
        Suite('node:tests-js', 'node-test', ['--test', '--test-reporter=spec', *js], ['bridge', 'model-base'], 900,
              needs_node=True, label='node --test tests/*.js（已登記的 %d 檔；不含夾具）' % len(js)),
        Suite('node:model_viewer', 'node-script', [NODE_SCRIPT_FILE], [], 300, needs_node=True, label=NODE_SCRIPT_FILE),
        Suite('node:polydraft', 'node-test', ['--test', '--test-reporter=spec', 'geometry-web/polydraft_test.js'],
              ['core'], 900, needs_node=True, label='geometry-web/polydraft_test.js'),
        Suite('node:canvas_direct', 'node-canvas', ['geometry-web/canvas_test.js', 'direct'], ['bridge'], 900,
              needs_node=True, label='geometry-web/canvas_test.js direct'),
    ]
    suites += [Suite(name, 'node-script', [file], [], 300, needs_node=True, label=file)
               for name, file in NODE_DOCUMENT_SCRIPT_FILES.items()]
    suites += [Suite(name, 'node-test', ['--test', '--test-reporter=spec', file], [], 300,
                     needs_node=True, label=file) for name, file in NODE_PURE_TEST_FILES.items()]
    return suites


# ------------------------------------------------------------------ environment

def inherited_geometry_vars():
    return sorted(k for k in os.environ if k.upper().startswith('GEOMETRY_'))


def child_env(infos, simulate_missing):
    """Children get the caller's environment MINUS every GEOMETRY_* variable, PLUS only what run_all itself sets.
    (A stale GEOMETRY_TEST_VIEWER / GEOMETRY_TEST_REFERENCE_WORKSPACE / GEOMETRY_BRIDGE in the shell must not leak in.)"""
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('GEOMETRY_')}
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env.update(binaries.env_vars(infos, only_fresh=True))
    for var in simulate_missing:
        env.pop(var, None)
    return env


def write_node_shim():
    """canvas_test.js direct hard-codes geometry-web/web_bridge.exe (a repo-local, possibly stale exe) and has no
    override.  This preload redirects exactly that spawn to GEOMETRY_TEST_BRIDGE and, only when it really rewrote the
    command, appends a line to the file named by GEOMETRY_SHIM_MARKER; run_all trusts the result only when it sees it."""
    shim = binaries.OUT_DIR / '_canvas_bridge_shim.cjs'
    shim.parent.mkdir(parents=True, exist_ok=True)
    shim.write_text(
        "const cp = require('child_process');\n"
        "const fs = require('fs');\n"
        "const orig = cp.spawn;\n"
        "cp.spawn = function (cmd, args, opts) {\n"
        "  const exe = process.env.GEOMETRY_TEST_BRIDGE;\n"
        "  const marker = process.env.GEOMETRY_SHIM_MARKER;\n"
        "  if (exe && typeof cmd === 'string' && /web_bridge\\.exe/i.test(cmd)) {\n"
        "    const before = cmd;\n"
        "    cmd = cmd.replace(/\"[^\"]*web_bridge\\.exe\"/i, () => '\"' + exe + '\"');\n"
        "    if (marker && cmd !== before) {\n"
        "      try { fs.appendFileSync(marker, 'REDIRECT ' + exe + '\\n'); } catch (e) { /* no marker => run_all distrusts the run */ }\n"
        "    }\n"
        "  }\n"
        "  return orig.call(this, cmd, args, opts);\n"
        "};\n", encoding='utf-8')
    return shim


# ------------------------------------------------------------------ result parsing

def sac_hits(text):
    """Keep environment hints without treating oracle rule names as environment errors.

    >>> sac_hits('[沒抓到!] C3_EDGE_UNSUPPORTED')
    []
    >>> sac_hits('UNSUPPORTED / BASE_COMPILER')
    ['BASE_COMPILER', 'UNSUPPORTED']
    >>> sac_hits('OSError: WinError 4551')
    ['WinError 4551']
    """
    return [face for face in SAC_FACES if face in text and
            (face != 'UNSUPPORTED' or re.search(r'(?<!\w)UNSUPPORTED(?!\w)', text))]


def parse_node_spec(text, row):
    def grab(label):
        m = re.search(r'^ℹ %s (\d+)\s*$' % label, text, re.M)
        return int(m.group(1)) if m else None
    total, passed, failed = grab('tests'), grab('pass'), grab('fail')
    cancelled, skipped, todo = grab('cancelled') or 0, grab('skipped') or 0, grab('todo') or 0
    if total is None:
        return False
    row.total, row.skipped = total, skipped + todo
    row.failed = (failed or 0) + cancelled
    row.passed = passed or 0
    for line in text.splitlines():
        if line.startswith('✖') and len(row.details) < 12:
            row.details.append(line.strip()[:200])
    return True


class ProcResult:
    def __init__(self, code, out, seconds, timed_out, reap_note=''):
        self.code, self.out, self.seconds, self.timed_out, self.reap_note = code, out, seconds, timed_out, reap_note


def kill_tree(proc):
    """Kill the process and every descendant (taskkill /T on Windows, the process group on POSIX)."""
    if IS_WIN:
        try:
            subprocess.run(['taskkill', '/T', '/F', '/PID', str(proc.pid)], capture_output=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass
    try:
        proc.kill()
    except OSError:
        pass


def _decode(data):
    return (data or b'').decode('utf-8', errors='replace')


def run_process(cmd, env, timeout, cwd=ROOT):
    started = time.time()
    kwargs = {} if IS_WIN else {'start_new_session': True}   # POSIX: own process group, so killpg reaches grandchildren
    try:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    except OSError as exc:
        return ProcResult(None, 'OSError: %s' % exc, time.time() - started, False)
    try:
        out_b, err_b = proc.communicate(timeout=timeout)
        return ProcResult(proc.returncode, _decode(out_b) + _decode(err_b), time.time() - started, False)
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        note = '已終止整棵行程樹（%s）' % ('taskkill /T /F' if IS_WIN else 'killpg SIGKILL')
        try:
            out_b, err_b = proc.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            # an escaped descendant still holds the output pipes: give up on the tail of the output, never hang
            out_b = err_b = b''
            note += '；有後代行程仍占著輸出管線，放棄收尾輸出'
            for pipe in (proc.stdout, proc.stderr):
                try:
                    pipe.close()
                except OSError:
                    pass
        return ProcResult(None, _decode(out_b) + _decode(err_b), time.time() - started, True, note)
    except BaseException:
        kill_tree(proc)    # Ctrl-C on run_all must not leave test processes behind
        raise


def classify_skips(suite_name, data):
    """How many of this unittest file's skips are covered by the named ALLOWED_SKIPS entries (each entry at most once)."""
    used, allowed = set(), 0
    for item in data.get('skip_items') or []:
        if item.get('scope') != 'test':
            continue
        for i, entry in enumerate(ALLOWED_SKIPS):
            if (i not in used and entry['suite'] == suite_name and entry['test'] == item.get('test')
                    and entry['reason'] in (item.get('reason') or '') and os.name in entry['platforms']):
                used.add(i)
                allowed += 1
                break
    return allowed


def run_suite(suite, env, infos):
    row = Row(suite.name, suite.counted)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / (suite.name.replace(':', '_') + '.log')
    marker = None

    if suite.kind == 'integrity':
        res = run_process([str(infos['integrity'].path)], env, suite.timeout)
    elif suite.kind == 'run_tests':
        # cwd = the output dir: the core writes current_geometry.svg into its working directory, and that must not be the repo root
        res = run_process([sys.executable, str(HERE / 'run_tests.py'), str(infos['core'].path)], env, suite.timeout,
                          cwd=binaries.OUT_DIR)
    elif suite.kind == 'unittest':
        json_path = LOG_DIR / (suite.name.replace(':', '_') + '.json')
        json_path.unlink(missing_ok=True)
        res = run_process([*suite.cmd, '--json-out', str(json_path), '--log', str(log_file.with_suffix('.unittest.log'))],
                          env, suite.timeout)
    elif suite.kind == 'mutation-check':
        mutation_env = dict(env)
        mutation_env['MUTATE_RESULTS'] = str(HERE / 'mutants_results.json')
        res = run_process(suite.cmd, mutation_env, suite.timeout)
    elif suite.kind == 'python-script':
        # The oracle reads rooms.json relative to its own directory.
        res = run_process(suite.cmd, env, suite.timeout, cwd=Path(suite.cmd[1]).parent)
    elif suite.kind == 'node-canvas':
        shim = write_node_shim()
        marker = LOG_DIR / 'canvas_shim.marker'
        marker.unlink(missing_ok=True)
        canvas_env = dict(env)
        canvas_env['GEOMETRY_SHIM_MARKER'] = str(marker)
        res = run_process([node_exe(), '--require', str(shim), *suite.cmd], canvas_env, suite.timeout)
    else:
        res = run_process([node_exe(), *suite.cmd], env, suite.timeout)
    code, out, secs, timed_out = res.code, res.out, res.seconds, res.timed_out
    row.seconds = secs
    row.ran = True
    log_file.write_text(out, encoding='utf-8')

    if timed_out:
        row.crashed = True
        row.failed = max(row.failed, 1)
        row.total = max(row.total, 1)
        row.note = '逾時（%d 秒）被終止，%s（%.1f 秒後收完）；日誌 %s' % (suite.timeout, res.reap_note, secs, log_file)
        return row

    if suite.kind == 'mutation-check':
        row.failed = int(code not in (0, 2))
        row.env_problem = code == 2
        row.note = 'mutation inventory freshness (not test assertions); exit %s' % code
        if code != 0:
            row.details = [line.strip() for line in out.splitlines()
                           if 'STALE ' in line or 'INVALID ' in line or 'BLOCKED ' in line][:10]
            row.note += '；日誌 %s' % log_file
        return row

    if suite.kind == 'integrity':
        m = re.search(r'(\d+)/(\d+) integrity checks passed', out)
        if m:
            row.passed, row.total = int(m.group(1)), int(m.group(2))
            row.failed = row.total - row.passed
            row.note = 'C 檢查點數（非 test 級）'
        else:
            row.crashed, row.total, row.failed = True, 1, 1
            row.note = '沒有看到結果行（exit %s）' % code
    elif suite.kind == 'run_tests':
        m = re.search(r'^GEOMETRY_TEST_RESULT (.*)$', out, re.M)
        if m:
            data = json.loads(m.group(1))
            row.total = data['total']
            row.passed = data['counts']['pass']
            row.failed = data['counts']['fail']
            infra = data['counts']['infrastructure']
            if infra:
                row.env_problem = True
                row.note = '環境／執行失敗 %d 案（run_tests exit %s）；' % (infra, code)
                row.skipped = infra
            for case in data['cases']:
                if case['status'] != 'pass' and len(row.details) < 10:
                    row.details.append('%s: %s' % (case['scene'], case['detail'][:160]))
        else:
            row.crashed, row.total, row.failed = True, 1, 1
            row.note = 'run_tests 沒有輸出結果行（exit %s）' % code
        if code == 2 and not row.env_problem:
            row.env_problem = True
            row.note += 'run_tests exit 2（環境失敗）；'
    elif suite.kind == 'unittest':
        json_path = LOG_DIR / (suite.name.replace(':', '_') + '.json')
        try:
            data = json.loads(json_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            row.crashed, row.total, row.failed = True, 1, 1
            row.note = 'runner 沒有產出結果（exit %s）：%s' % (code, out.strip().splitlines()[-1][:160] if out.strip() else '')
            return row
        row.total, row.passed, row.failed, row.skipped = data['total'], data['passed'], data['failed'], data['skipped']
        for f in data.get('failures', [])[:12]:
            row.details.append('%s [%s] %s' % (f['test'], f['kind'], f['message'][:160]))
        if data.get('import_error'):
            row.crashed = True
            row.note = '模組載入失敗；'
        if data['skipped']:
            reasons = '；'.join('%s ×%d' % (r[:70], n) for r, n in list(data.get('skip_reasons', {}).items())[:2])
            row.note += 'skip：%s' % reasons
            if data.get('skip_count_basis') == 'ast':
                row.note += '（模組載入時就 SkipTest：test 數由 AST 數出）'
            elif data.get('skip_count_basis') == 'at-least-1':
                row.note += '（模組載入時就 SkipTest：數不出 test 數，「至少 1」）'
            row.allowed_skips = classify_skips(suite.name, data)
            if row.allowed_skips:
                row.note += '（其中 %d 個在具名允許清單，平台固有，不計入 exit 3）' % row.allowed_skips
        if data.get('blocked_by_error'):
            row.note += ' 另有 %d 個 test 因 setUpClass 錯誤未執行（已計入 fail）' % data['blocked_by_error']
    elif suite.kind in ('node-test', ):
        if not parse_node_spec(out, row):
            row.crashed, row.total, row.failed = True, 1, 1
            row.note = 'node 沒有輸出摘要（exit %s）' % code
    elif suite.kind in ('node-script', 'python-script'):
        row.passed, row.failed = (1 if code == 0 else 0), (0 if code == 0 else 1)
        row.note = '僅結束碼：腳本式，無 test 級計數，以 exit code 判定'
        if code:
            if suite.kind == 'python-script':
                # Keep the oracle's named mutant/check failure, even when the final sweep is green.
                row.details.extend(line[:200] for line in out.strip().splitlines()[-12:])
            else:
                row.details.append(out.strip().splitlines()[-1][:200] if out.strip() else '')
    elif suite.kind == 'node-canvas':
        m = re.search(r'(\d+) pass / (\d+) fail', out)
        if m:
            row.passed, row.failed = int(m.group(1)), int(m.group(2))
            row.total = row.passed + row.failed
            for line in out.splitlines():
                if line.lstrip().startswith('FAIL') and len(row.details) < 10:
                    row.details.append(line.strip()[:200])
        else:
            row.crashed, row.total, row.failed = True, 1, 1
            row.note = 'canvas_test 沒有輸出摘要（exit %s）' % code
        # did the preload really redirect the spawn?  Only the marker file it writes counts as proof.
        want = env.get('GEOMETRY_TEST_BRIDGE')
        seen = []
        try:
            seen = [ln.strip() for ln in marker.read_text(encoding='utf-8').splitlines() if ln.strip()]
        except OSError:
            pass
        if want and ('REDIRECT ' + want) in seen:
            row.note = ('斷言數；preload 已把 web_bridge.exe 的 spawn 轉向 %s（標記檔 %d 筆為證）' % (want, len(seen))) + (
                '；' + row.note if row.note else '')
        else:
            row.env_problem = True
            why = ('GEOMETRY_TEST_BRIDGE 未設定' if not want else '沒有留下轉向標記')
            row.note = ('環境：canvas shim 沒有攔到 bridge 的 spawn（%s；canvas_test.js 啟動 bridge 的寫法可能變了）——'
                        '這次結果可能來自 geometry-web/web_bridge.exe，不採信' % why) + ('；' + row.note if row.note else '')
    if row.counted and row.total == 0 and not row.crashed:
        row.crashed = True
        row.failed = max(row.failed, 1)
        row.note += '；發現 0 個測試（0 個 test 不算通過）'
        row.details.append('這個 suite 沒有發現任何測試')
    if code not in (0, None) and not row.failed and not row.crashed and not row.env_problem and suite.kind != 'run_tests':
        # exit code nonzero but no failed test recorded (e.g. tearDownModule, process abort): never call that green
        row.crashed = True
        row.failed = max(row.failed, 1)
        row.note += '；子行程 exit %s 但沒有記到失敗的 test' % code
    if row.failed or row.crashed:
        hits = sac_hits(out + '\n' + ' '.join(row.details))
        if hits:
            row.note += '；疑似環境阻擋（命中：%s）' % '、'.join(hits)
    if row.failed or row.crashed or row.skipped or row.env_problem:
        row.note += '；日誌 %s' % log_file
    row.note = row.note.strip('；; ')
    return row


# ------------------------------------------------------------------ expected counts

def load_expected():
    """(data or None, error message or '')"""
    try:
        data = json.loads(EXPECTED_FILE.read_text(encoding='utf-8'))
    except OSError:
        return None, '找不到 %s（先做一次完整跑再加 --update-expected 產生）' % EXPECTED_FILE.name
    except ValueError as exc:
        return None, '%s 不是合法 JSON：%s' % (EXPECTED_FILE.name, exc)
    if not isinstance(data.get('suites'), dict):
        return None, '%s 缺少 "suites" 物件' % EXPECTED_FILE.name
    return data, ''


def compare_expected(rows, suites, expected, err, full):
    """Strict equality of each suite's discovered count with run_all.expected.json.  Returns [(suite, message)]."""
    if expected is None:
        return [('(expected 檔)', err)]
    entries = expected['suites']
    by_name = {s.name: s for s in suites}
    problems = []
    for r in rows:
        s = by_name[r.name]
        if s.name.startswith('extra:') or not r.ran or r.crashed or r.env_problem:
            continue   # extras are unregistered by design; crashed/env rows are already red/exit 2
        e = entries.get(r.name)
        if e is None:
            msg = '沒有登記在 %s（新 suite 必須明確登記預期數；--update-expected）' % EXPECTED_FILE.name
        elif not s.counted:
            msg = '' if e.get('mode') == 'exit-code-only' else 'expected 對這個「僅結束碼」suite 登記成 %r，應為 exit-code-only' % e.get('mode')
        elif e.get('mode') != 'count' or not isinstance(e.get('count'), int):
            msg = 'expected 登記的是 %r，但這個 suite 有計數，應為 {"mode":"count","count":N}' % e
        elif r.total != e['count']:
            msg = '預期 %d、實得 %d（%s；新增／減少 test 後須明確 --update-expected）' % (e['count'], r.total, UNIT.get(s.kind, ''))
        else:
            msg = ''
        if msg:
            r.expected_problem = msg
            problems.append((r.name, msg))
    if full:
        for name in entries:
            if name not in by_name:
                problems.append((name, '%s 登記了這個 suite，但 run_all 已沒有它' % EXPECTED_FILE.name))
    return problems


def update_expected(rows, suites, registry_errors):
    """Rewrite run_all.expected.json from a complete run.  Refuses when the run cannot be trusted as a census."""
    blockers = list(registry_errors)
    for r in rows:
        if not r.ran:
            blockers.append('%s 沒有跑（%s）' % (r.name, r.note))
        elif r.env_problem or r.crashed:
            blockers.append('%s 有環境問題／崩潰／逾時（%s）' % (r.name, r.note[:100]))
        elif not r.counted and r.failed:
            blockers.append('%s 僅結束碼驗收失敗（%s）' % (r.name, r.note[:100]))
        elif r.counted and r.total == 0:
            blockers.append('%s 發現 0 個測試' % r.name)
        elif r.skipped - r.allowed_skips > 0:
            blockers.append('%s 有 %d 個不在允許清單的 skip' % (r.name, r.skipped - r.allowed_skips))
    if blockers:
        print('\n--update-expected 拒絕執行（這次跑不能當作數量的依據）：')
        for b in blockers:
            print('  - %s' % b)
        return False
    old, _ = load_expected()
    old_entries = old['suites'] if old else {}
    suites_out = {}
    for s, r in zip(suites, rows):
        suites_out[s.name] = ({'mode': 'exit-code-only'} if not s.counted
                              else {'mode': 'count', 'count': r.total, 'unit': UNIT.get(s.kind, '')})
    data = {
        '_說明': 'run_all.py 的各 suite「發現到的測試／斷言數」；完整跑時逐 suite 嚴格相等，不符即 fail。'
                 '新增或刪除測試後請在一次完整跑之後用 --update-expected 明確更新（並在 commit 中說明）。'
                 'exit-code-only 表示該 suite 只有結束碼、沒有可數的 test。',
        'suites': suites_out,
    }
    EXPECTED_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('\n已重寫 %s：' % EXPECTED_FILE)
    changed = False
    for name, e in suites_out.items():
        before = old_entries.get(name)
        if before != e:
            changed = True
            print('  %-24s %s -> %s' % (name, before if before else '(新)', e))
    for name in old_entries:
        if name not in suites_out:
            changed = True
            print('  %-24s %s -> (移除)' % (name, old_entries[name]))
    if not changed:
        print('  （與原檔相同）')
    failing = [r.name for r in rows if r.failed]
    if failing:
        print('  注意：下列 suite 目前有 fail，但仍照實記下「發現到的數量」（fail 與數量無關）：%s' % '、'.join(failing))
    return True


# ------------------------------------------------------------------ table

def width(text):
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in text)


def pad(text, size, right=False):
    gap = ' ' * max(0, size - width(text))
    return gap + text if right else text + gap


def print_table(rows):
    header = ['suite', '測試數', 'pass', 'fail', 'skip', '秒', '備註']
    body = []
    for r in rows:
        note = r.note
        if r.ran and not r.counted:
            body.append([r.name, '-', 'ok' if r.passed else '-', 'FAIL' if r.failed else '-', '-', '%.1f' % r.seconds, note])
        elif r.ran:
            if r.expected_problem:
                note = ('預期數不符：' + r.expected_problem + ('；' + note if note else ''))
            body.append([r.name, str(r.total), str(r.passed), str(r.failed), str(r.skipped), '%.1f' % r.seconds, note])
        else:
            body.append([r.name, '-', '-', '-', '-', '-', note])
    counted = [r for r in rows if r.ran and r.counted]
    tot = [sum(r.total for r in counted), sum(r.passed for r in counted), sum(r.failed for r in counted),
           sum(r.skipped for r in counted), sum(r.seconds for r in rows if r.ran)]
    body.append(['合計(已執行、有計數者)', str(tot[0]), str(tot[1]), str(tot[2]), str(tot[3]), '%.1f' % tot[4], ''])
    body.append(['未納入', '-', '-', '-', '-', '-', '需 Chrome，另行執行：geometry-web/cdp_test.js、geometry-web/space_model_test.js'])
    sizes = [max(width(row[i]) for row in body + [header]) for i in range(6)]
    def fmt(row):
        cells = [pad(row[0], sizes[0])] + [pad(row[i], sizes[i], right=True) for i in range(1, 6)] + [row[6]]
        return '  '.join(cells).rstrip()
    print(fmt(header))
    print('-' * min(150, sum(sizes) + 12))
    for row in body[:-2]:
        print(fmt(row))
    print('-' * min(150, sum(sizes) + 12))
    print(fmt(body[-2]))
    print(fmt(body[-1]))
    print('必要 owner／browser 整合與模組驗證另驗（不計入上述 pass/skip）：')
    for stem,reason in PY_BROWSER_GATES.items():
        print('  tests/%s.py：%s；獨立執行，本 aggregate 未驗。' % (stem,reason))
    for rel,count in REQUIRED_OWNER_GATES.items():
        print('  %s：%d項 required；source-rooms owner 接口未實作時 exit3/pending_implementation，不是環境 skip或pass。' % (rel,count))
    for rel in sorted(NODE_EXCLUDED):
        if rel.startswith('tests/test_issue77_') or rel in ('tests/scenario_browser_check.cjs', 'tests/test_scenario_grid_interface.js'):
            print('  %s：%s；獨立執行，本 aggregate 未驗。' % (rel, NODE_EXCLUDED[rel]))
    for rel, count in REQUIRED_BROWSER_GATES.items():
        scope = BROWSER_GATE_SCOPES[rel]
        print('  %s：%d %s checks required；本 aggregate 未驗。' % (rel, count, scope))


# ------------------------------------------------------------------ main

def partial_flags(args):
    flags = []
    if args.only:
        flags.append('--only ' + ' --only '.join(args.only))
    for extra in args.extra_py:
        flags.append('--extra-py ' + extra)
    for var in args.simulate_missing:
        flags.append('--simulate-missing ' + var)
    return flags


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--build', action='store_true', help='先建置 stale/missing 的二進位（沿用 fresh 的，不碰）')
    parser.add_argument('--only', action='append', default=[], metavar='SUBSTR', help='只跑名稱含此子字串的 suite（可重複；局部跑，不能當完整驗收）')
    parser.add_argument('--list', action='store_true', help='列出 suite 與其需要的二進位後結束')
    parser.add_argument('--allow-skip', action='store_true', help='skip 不影響 exit code')
    parser.add_argument('--extra-py', action='append', default=[], metavar='FILE',
                        help='另外加一個 unittest 檔（例如放在 %%TEMP%% 的故意失敗檔，用來驗證 fail 會被報出來；示範跑，不能當完整驗收）')
    parser.add_argument('--simulate-missing', action='append', default=[], metavar='ENVVAR',
                        help='模擬缺少某環境變數（僅供驗證 skip 是否可見；示範跑，exit code 絕不為 0）')
    parser.add_argument('--update-expected', action='store_true',
                        help='完整跑之後重寫 tests/run_all.expected.json（不能與 --only／--extra-py／--simulate-missing 併用）')
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    partial = partial_flags(args)
    if args.update_expected and partial:
        print('--update-expected 只能在完整跑使用；你同時給了：%s' % '、'.join(partial))
        return 2
    registry_errors = check_registry()

    suites = build_suites()
    for extra in args.extra_py:
        extra_path = Path(extra).resolve()
        suites.append(Suite('extra:' + extra_path.stem, 'unittest', [sys.executable, str(RUNNER), str(extra_path)], [], 300,
                            label=str(extra_path)))
    if args.only:
        suites = [s for s in suites if any(sub in s.name for sub in args.only)]
    if args.list:
        for s in suites:
            print('%-32s 需要：%-22s %s' % (s.name, ', '.join(s.needs) or '-', s.label + ('（需 node）' if s.needs_node else '')))
        print('%-32s 未納入（需 Chrome）：geometry-web/cdp_test.js、geometry-web/space_model_test.js' % '-')
        print('必要正式整合入口：tests/integration/issue77_attachment_owner.js（5項；未實作時 exit3）')
        print('另外4個 #77 真瀏覽器入口：見 tests/INTEGRATION-GATES.md；本命令未驗。')
        for rel, count in REQUIRED_BROWSER_GATES.items():
            scope = BROWSER_GATE_SCOPES[rel]
            print('  %s：%d %s checks required；本 aggregate 未驗。' % (rel, count, scope))
        for p in registry_errors:
            print('登記問題：%s' % p)
        return 1 if registry_errors else 0
    if not suites:
        print('沒有名稱含 %s 的 suite（用 --list 看全部）' % args.only)
        return 2
    try:
        with binaries.ProcessLock('run_all'):
            return run(args, suites, registry_errors, partial)
    except binaries.LockBusy as exc:
        print('錯誤：%s' % exc)
        return 2


def run(args, suites, registry_errors, partial):
    # which binaries the selected suites need (a binary whose every env variable is simulated-missing is not needed)
    simulated = set(args.simulate_missing)
    ignored = {b.name for b in binaries.REGISTRY if b.envs and all(v in simulated for v in b.envs)}
    needed = sorted({n for s in suites for n in s.needs if n not in ignored} | ({'core'} if any(s.kind == 'run_tests' for s in suites) else set()))
    print('二進位輸出目錄：%s' % binaries.OUT_DIR)
    if args.build:
        print('[build] 只建置 stale/missing：%s' % ', '.join(needed))
        try:
            with binaries.ProcessLock('build'):
                results = binaries.build(needed)
        except binaries.LockBusy as exc:
            print('錯誤：%s' % exc)
            return 2
        for name, r in results.items():
            head = r.detail.splitlines()[0] if r.detail else ''
            print('  %-10s %-14s %s' % (name, r.status, head))
    infos = binaries.inspect_all()
    print('[binaries]')
    for name in needed:
        info = infos[name]
        print('  %-10s %-8s %s' % (name, info.state, info.reason))

    env = child_env(infos, simulated)
    cleared = inherited_geometry_vars()
    print('[環境] CC=%s（繼承自外殼；僅影響 binaries.py 在非 Windows 的編譯）' % (os.environ.get('CC') or '未設定'))
    print('[環境] 已清除外殼繼承的 GEOMETRY_*：%s' % ('、'.join(cleared) or '（無）'))
    print('[環境] run_all 設給子行程的 GEOMETRY_*：%s' % ('、'.join(sorted(k for k in env if k.startswith('GEOMETRY_'))) or '（無）'))
    for var in ('NODE_OPTIONS', 'PYTHONPATH', 'PYTHONSTARTUP'):
        if os.environ.get(var):
            print('[環境] 注意：外殼設了 %s=%s，子行程會繼承' % (var, os.environ[var]))
    if registry_errors:
        print('\n登記檢查失敗（run_all 直接判 fail；修法：把檔案明確登記進 run_all.py）：')
        for p in registry_errors:
            print('  - %s' % p)
        print()

    rows = []
    stale_fix = False
    try:
        for i, s in enumerate(suites, 1):
            row = Row(s.name, s.counted)
            blockers = [n for n in s.needs if n not in ignored and infos[n].state not in ('fresh', 'n/a')]
            if s.needs_node and not node_exe():
                row.env_problem = True
                row.note = '環境：缺 node'
            elif blockers:
                row.env_problem = True
                stale_fix = True
                row.note = '環境：二進位過期或缺少，未跑（%s；修法：加 --build 或 python tests/binaries.py build）' % '、'.join(
                    '%s=%s' % (n, infos[n].state) for n in blockers)
            else:
                print('[%d/%d] %s …' % (i, len(suites), s.name), flush=True)
                row = run_suite(s, env, infos)
            rows.append(row)
    except KeyboardInterrupt:
        print('\n被中斷：已終止正在跑的行程樹；此次不產生結論。')
        return 130

    full = not partial
    expected_problems = []
    updated = None
    if args.update_expected:
        updated = update_expected(rows, suites, registry_errors)
    else:
        expected, exp_err = load_expected()
        expected_problems = compare_expected(rows, suites, expected, exp_err, full)

    print()
    print_table(rows)
    failed_rows = [r for r in rows if r.details and (r.failed or r.crashed)]
    if failed_rows:
        print('\n失敗明細（每個 suite 至多前幾筆，完整內容見日誌）：')
        for r in failed_rows:
            print('  %s' % r.name)
            for d in r.details[:8]:
                print('    - %s' % d)
    if expected_problems:
        print('\n預期數不符（%s）：' % EXPECTED_FILE.name)
        for name, msg in expected_problems:
            print('  %s：%s' % (name, msg))
    if registry_errors:
        print('\n未登記／登記有誤的測試檔（判 fail）：')
        for p in registry_errors:
            print('  - %s' % p)
    if stale_fix:
        print('\n有 suite 因二進位過期／缺少而未跑：執行 python tests/run_all.py --build（或 python tests/binaries.py build）。')

    any_fail = (any(r.failed or r.crashed for r in rows) or bool(expected_problems) or bool(registry_errors)
                or (args.update_expected and not updated))
    any_env = any(r.env_problem for r in rows)
    any_skip = any(r.skipped - r.allowed_skips > 0 for r in rows if r.ran)
    if any_fail:
        code = 1
    elif any_env:
        code = 2
    elif any_skip and not args.allow_skip:
        code = 3
    elif args.simulate_missing:
        code = 4
    else:
        code = 0
    if partial:
        print('\n==== 部分／示範執行，不可當完整驗收 ====')
        print('使用了：%s' % '；'.join(partial))
        meaning = {
            0: '所選 suite 沒有 fail、沒有環境問題、沒有可避免的 skip（只代表所選範圍，沒選到的沒跑）',
            1: '有 fail／預期數不符／未登記檔', 2: '有環境阻擋／二進位過期', 3: '所選範圍只有 skip（沒有 fail）',
            4: '--simulate-missing 示範跑：結果只供檢視 skip 是否看得見（部分測試缺變數時會改用舊預設 exe），刻意不回 0',
        }[code]
    else:
        meaning = {
            0: '完整非瀏覽器登錄測試：全部 suite 都跑了、數量與 expected 相符、沒有 fail、沒有環境問題、沒有可避免的 skip（具名允許清單不算）；必要正式 owner／瀏覽器整合另驗',
            1: '有 fail／逾時／預期數不符／未登記檔', 2: '有環境阻擋／二進位過期', 3: '只有 skip（沒有 fail）',
        }[code]
    if args.allow_skip and code == 0 and any_skip:
        skipped_total = sum(r.skipped - r.allowed_skips for r in rows if r.ran)
        meaning = '沒有 fail，但有 %d 個 skip 被 --allow-skip 放行：不等於全部都跑過' % skipped_total
    elif args.allow_skip:
        meaning += '；注意：本次用了 --allow-skip，skip 已不影響結果'
    print('\nexit %d：%s' % (code, meaning))
    return code


if __name__ == '__main__':
    sys.exit(main())
