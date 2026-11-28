#!/usr/bin/env python3
"""Bounded named withdrawals of X4 guards; local observations, not CI receipts.

Each change is applied to a tiny isolated copy. A kill requires a completed
unittest assertion with the named diagnostic, never an import/crash/timeout.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
TOOL = "geometry-guide/axiom_traceability.py"
MATRIX = "geometry-guide/axiom_matrix.py"
TEST = "tests/test_axiom_traceability.py"
C = "AxiomTraceabilityContracts."
P = "AxiomMatrixClauseParsingTests."

# ID, source, unique old/new bytes, actual judge, required assertion marker.
CASES = [
    ("X4-PARSER-BOLD-IR", MATRIX, r'\*\*([DIR]\d+[a-z]?)\s', r'\*\*(D\d+[a-z]?)\s',
     P + "test_current_ssot_keeps_five_bold_ir_clauses_separate", "X4_PARSER_CURRENT_FIVE_BOLD_IR"),
    ("X4-PARSER-SUFFIX", MATRIX, r'\*\*([DIR]\d+[a-z]?)\s', r'\*\*([DIR]\d+)\s',
     P + "test_heading_forms_suffixes_and_plain_d_references", "X4_PARSER_HEADING_FORMS_AND_SUFFIXES"),
    ("X4-PARSER-PLAIN-D-BODY", MATRIX, r'^([IR]\d+[a-z]?)\s', r'^([DIR]\d+[a-z]?)\s',
     P + "test_heading_forms_suffixes_and_plain_d_references", "X4_PARSER_HEADING_FORMS_AND_SUFFIXES"),
    ("X4-PARSER-SECTION-BOUNDARY", MATRIX, 'elif re.match(r"^## ", ln) and marks:', 'elif False:',
     P + "test_bodies_stop_at_next_clause_or_section", "X4_PARSER_SECTION_BOUNDARY"),
    ("X4-STATUS-MISSING", TOOL, '    if missing:\n', '    if False and missing:\n',
     C + "test_new_clause_without_marker_is_rejected", "X4_STATUS_MISSING"),
    ("X4-STATUS-DUPLICATE", TOOL, '            if cid in result:\n', '            if False and cid in result:\n',
     C + "test_duplicate_marker_is_rejected_across_fragments", "X4_STATUS_DUPLICATE"),
    ("X4-STATUS-STALE-CLAUSE", TOOL, '            if item["body_sha256"] != ax[cid]["body_sha256"]:',
     '            if False and item["body_sha256"] != ax[cid]["body_sha256"]:',
     C + "test_changed_clause_body_invalidates_old_marker", "X4_STATUS_STALE_CLAUSE"),
    ("X4-STATUS-UNKNOWN", TOOL, '            if cid not in ax:\n                reject("X4_STATUS_UNKNOWN_CLAUSE", cid)',
     '            if cid not in ax:\n                continue',
     C + "test_marker_for_unknown_clause_is_rejected", "X4_STATUS_UNKNOWN_CLAUSE"),
    ("X4-STATUS-ENUM", TOOL, 'or item["status"] not in STATES', 'or False',
     C + "test_invalid_status_schema_keys_and_state_are_rejected", "X4_STATUS_SCHEMA"),
    ("X4-STATUS-IMPLEMENTATION-EVIDENCE", TOOL,
     'if item["status"] in {"implemented", "partial"} and "implementation" not in kinds:',
     'if False and item["status"] in {"implemented", "partial"} and "implementation" not in kinds:',
     C + "test_implemented_and_partial_require_reviewed_implementation", "X4_STATUS_SCHEMA"),
    ("X4-STATUS-ABSENCE-EVIDENCE", TOOL, 'if item["status"] == "unimplemented" and (',
     'if False and item["status"] == "unimplemented" and (',
     C + "test_unimplemented_needs_scoped_absence_evidence_and_rejects_implementation", "X4_STATUS_SCHEMA"),
    ("X4-REVIEW-FRESHNESS", TOOL, 'effective = marker["status"] if fresh else "unreviewed"',
     'effective = marker["status"]',
     C + "test_changed_evidence_downgrades_effective_status_without_rejecting_guard", "X4_STALE_REVIEW_CANNOT_ASSERT_IMPLEMENTED"),
    ("X4-FINDING-FRESHNESS", TOOL, 'state=row["state"] if current else "review_required"',
     'state=row["state"]',
     C + "test_findings_with_stale_sources_require_review", "X4_STALE_FINDING_CANNOT_REMAIN_FIXED"),
    ("X4-EVIDENCE-HASH-CLOSURE", TOOL, 'input_hashes[link["path"]] = link["current_source_sha256"]',
     'pass  # withdrawn evidence hash inclusion',
     C + "test_reviewed_evidence_outside_inventory_changes_source_digest", "X4_INCLUDE_REVIEWED_STATUS_SOURCE"),
    ("X4-TEXT-CANNOT-PROMOTE", TOOL, 'effective = marker["status"] if fresh else "unreviewed"',
     'effective = "implemented" if any(hits[cid].values()) else marker["status"]',
     C + "test_cross_layer_candidates_keep_named_judges_and_do_not_promote_status", "X4_REFERENCE_AND_REVIEW_LABEL_DO_NOT_PROMOTE"),
    ("X4-CANVAS-TEST-ROLE", TOOL, ' or "canvas_sections" in parts', '',
     C + "test_cross_layer_candidates_keep_named_judges_and_do_not_promote_status", "X4_ALL_IMPLEMENTATION_LAYERS_AND_NO_TEST_MISCLASSIFICATION"),
    ("X4-BROWSER-TEST-ROLE", TOOL, ', "_browser_check.js", "_browser_test.py"', '',
     C + "test_browser_judges_are_test_candidates", "X4_BROWSER_JUDGES_STAY_IN_TEST_COLUMN"),
    ("X4-MUTATOR-NOT-JUDGE", TOOL, '\n            or name == "mutate.py" or name.startswith("mutate_")', '',
     C + "test_mutation_definition_is_named_but_not_an_execution_receipt", "X4_MUTATOR_IS_NOT_TEST_JUDGE"),
    ("X4-EXACT-TOKEN", TOOL,
     'pattern = re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(map(re.escape, ids)) + r")(?![A-Za-z0-9_])")',
     'pattern = re.compile("|".join(map(re.escape, ids)))',
     C + "test_clause_tokens_do_not_match_prefixes_or_identifier_substrings", "X4_EXACT_CLAUSE_TOKEN_BOUNDARY"),
    ("X4-NAMED-MUTATION", TOOL, 'and ("old" in item or "retired" in item)):', 'and False):',
     C + "test_mutation_definition_is_named_but_not_an_execution_receipt", "X4_SINGLE_QUOTED_NAMED_MUTATION_DEFINITION"),
    ("X4-SYMLINK-EVIDENCE", TOOL, '        if path.is_symlink():', '        if False and path.is_symlink():',
     C + "test_symlink_evidence_is_rejected", "X4_PATH_UNSAFE"),
    ("X4-ACCEPT-NO-DEAD-ERROR", "tests/run_tests.py",
     "{'scene': '_edge_grid_panel_odd_gap.scene', 'expect': 'accept', 'lengths': [],",
     "{'scene': '_edge_grid_panel_odd_gap.scene', 'expect': 'accept', 'error': '縫寬必須是偶數', 'lengths': [],",
     C + "test_accepted_scene_specs_do_not_carry_ignored_rejection_fields", "X4_ACCEPT_HAS_NO_REJECTION_ERROR"),
    ("X4-FINDING-CLAUSE-VERSION", TOOL,
     'clause_fresh = all(row["clause_sha256"][cid] == ax[cid]["body_sha256"] for cid in row["clauses"])',
     'clause_fresh = True',
     C + "test_findings_track_clause_versions", "X4_CHANGED_CLAUSE_CANNOT_KEEP_OLD_FINDING_FIXED"),
    ("X4-SCENE-JUDGE-LINK", TOOL, 'kinds["test"].extend(scene_owners[item["path"]])',
     'pass  # withdrawn registered scene judge link',
     C + "test_scene_reference_links_to_the_registered_judge_without_claiming_execution", "X4_SCENE_LINKS_TO_ITS_REAL_JUDGE"),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(root, judge, output):
    command = [sys.executable, "-B", str(root / TEST), judge, "-v"]
    started = time.monotonic()
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, timeout=90, env=environment)
        raw, code = result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired as error:
        raw, code = (error.stdout or b"") + (error.stderr or b"") + b"\nX4_WITHDRAWAL_TIMEOUT\n", 124
    output.write_bytes(raw)
    return {"command": command, "cwd": str(root), "exit": code,
            "seconds": round(time.monotonic() - started, 6), "log": output.name,
            "bytes": len(raw), "sha256": sha(raw)}, raw.decode("utf-8", "replace")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", choices=[row[0] for row in CASES])
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    cases = [row for row in CASES if not args.only or row[0] == args.only]
    results = []
    with tempfile.TemporaryDirectory(prefix="x4-withdrawals-") as temporary:
        isolated = Path(temporary)
        inputs = {}
        for relative in (TOOL, MATRIX, TEST, "tests/run_tests.py", "公理層.md"):
            original = (ROOT / relative).read_bytes()
            target = isolated / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(original)
            inputs[relative] = sha(original)
        for identifier, relative, old, new, judge, marker in cases:
            target = isolated / relative
            original = target.read_bytes()
            before = original.decode("utf-8")
            if before.count(old) != 1:
                raise ValueError("X4_WITHDRAWAL_ANCHOR_NOT_UNIQUE: " + identifier)
            phases = []
            try:
                first, _ = run(isolated, judge, args.out / (identifier + "-before.log"))
                phases.append(first)
                target.write_text(before.replace(old, new, 1), encoding="utf-8", newline="")
                second, red = run(isolated, judge, args.out / (identifier + "-withdrawn.log"))
                phases.append(second)
            finally:
                target.write_bytes(original)
            third, _ = run(isolated, judge, args.out / (identifier + "-restored.log"))
            phases.append(third)
            exits = [row["exit"] for row in phases]
            killed = (exits == [0, 1, 0] and "AssertionError" in red and marker in red
                      and "FAILED (failures=" in red and "ERROR:" not in red
                      and "ImportError" not in red and "ModuleNotFoundError" not in red
                      and "X4_WITHDRAWAL_TIMEOUT" not in red)
            row = {"id": identifier, "source": relative, "judge": judge, "assertion": marker,
                   "old": old, "new": new, "phases": phases, "exits": exits, "killed": killed}
            results.append(row)
            print(identifier + ": " + str(exits) + " " + ("killed" if killed else "BLOCKED"), flush=True)
    value = {"schema": "geometry-x4-local-withdrawals/1", "acceptance": False,
             "not_mutation_workflow_receipt": True, "inputs": inputs, "results": results}
    (args.out / "results.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if results and all(row["killed"] for row in results) else 1


if __name__ == "__main__":
    sys.exit(main())
