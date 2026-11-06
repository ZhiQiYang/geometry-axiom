"""#360 strict contract mutations. Requires an independently built current bridge.

No source, golden, expected inventory or official mutation ledger is rewritten.
Every mutant must complete one real unittest with an AssertionError, no errors
or skips; the same test is run before and after restoring the exact input.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tests import test_geo261_mutation_migration as migration
from tests import test_engineering_terminal as terminal

METHOD = "test_all_fifty_definitions_keep_live_or_retired_targets"
K1_METHOD = "test_readonly_and_external_baseline_replies"


def run(case, method, phase, expected_oracle):
    result = unittest.TestResult()
    test = case(method)
    expected_test = test.id()
    unittest.TestSuite([test]).run(result)
    if (result.testsRun != 1 or result.errors or result.skipped
            or result.expectedFailures or result.unexpectedSuccesses):
        raise AssertionError("infrastructure is not a kill: " + repr(vars(result)))
    failures = [trace for _, trace in result.failures]
    if phase == "mutant":
        if len(result.failures) != 1:
            raise AssertionError("exactly one named assertion must fail: " + repr(failures))
        failed_test, trace = result.failures[0]
        if failed_test.id() != expected_test or "AssertionError" not in trace:
            raise AssertionError("wrong test or non-assertion failure: " + repr(result.failures))
        diagnostic = trace.rsplit("AssertionError", 1)[1]
        if expected_oracle not in diagnostic:
            raise AssertionError("wrong assertion oracle: " + expected_oracle + "\n" + trace)
    elif failures:
        raise AssertionError("baseline/restored failed: " + "\n".join(failures))
    return {"exit": int(bool(failures)), "testsRun": result.testsRun,
            "expectedTest": expected_test, "expectedOracle": expected_oracle,
            "expectedFailures": [], "failures": failures}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--only", choices=("inventory", "terminal", "all"), default="all")
    args = parser.parse_args()
    rows = []
    if args.only in ("inventory", "all"):
        original = copy.deepcopy(migration.mutate.MUTANTS)
        first = "R09A_N01_ZERO_ID_REOPEN"

        def altered(kind):
            entries = copy.deepcopy(original)
            row = next(item for item in entries if item["id"] == first)
            if kind == "missing":
                entries.remove(row)
            elif kind == "duplicate":
                entries.append(copy.deepcopy(row))
            elif kind == "unknown":
                extra = copy.deepcopy(row)
                extra["id"] = "R09A_UNREVIEWED"
                entries.append(extra)
            elif kind == "owner":
                row["file"] = "current_geometry.c"
            elif kind == "binary":
                del row["binary"]
            elif kind == "judge":
                row["tests"] = ["tests.test_identity_ledger.IdentityLedger.test_scene_roundtrip"]
            elif kind == "exemption":
                row["equivalent"] = "not a reviewed exemption"
            elif kind == "legacy":
                next(item for item in entries if item["id"] == "M01")["file"] = "current_geometry.c"
            return entries

        oracles = {
            "missing": "R360_NATIVE_IDENTITY_NO_MISSING_IDS",
            "duplicate": "R360_NATIVE_NO_DUPLICATE_IDS",
            "unknown": "R360_ORIGINAL_123_OWNERS_UNCHANGED",
            "owner": first + " native owner",
            "binary": first + " must execute the native bridge",
            "judge": first + " exact behavioral judges",
            "exemption": first + " must execute, not be exempted",
            "legacy": "R360_ORIGINAL_123_OWNERS_UNCHANGED",
        }
        for kind, oracle in oracles.items():
            case = migration.LiveMutationAnchorMigration
            baseline = run(case, METHOD, "baseline", oracle)
            with mock.patch.object(migration.mutate, "MUTANTS", altered(kind)):
                mutant = run(case, METHOD, "mutant", oracle)
            restored = run(case, METHOD, "restored", oracle)
            mid = "R360_NATIVE_INVENTORY_" + kind.upper()
            rows.append({"id": mid, "baseline": baseline, "mutant": mutant, "restored": restored})
            print(mid, baseline["exit"], mutant["exit"], restored["exit"], flush=True)

    if args.only in ("terminal", "all"):
        fixture = ROOT / "tests/fixtures/k1_terminal_legacy_replies.json"
        if hashlib.sha256(fixture.read_bytes()).hexdigest() != "06dd2e1a96d4f739f5ce4a5f87fba3e941f0e0411d332c7ce545985d877de4fc":
            raise AssertionError("K1 independent external baseline bytes changed")
        baseline = run(terminal.EngineeringTerminal, K1_METHOD, "baseline", "K1-a: non-terminal fields/order changed")
        # Remove exactly the new extension projection; do not change the
        # immutable baseline or the product's I72 capability announcement.
        with mock.patch.object(terminal, "project_identity_capability", side_effect=lambda case, value: value):
            mutant = run(terminal.EngineeringTerminal, K1_METHOD, "mutant", "K1-a: non-terminal fields/order changed")
        restored = run(terminal.EngineeringTerminal, K1_METHOD, "restored", "K1-a: non-terminal fields/order changed")
        mid = "R360_K1_REVIEWED_IDENTITY_PROJECTION"
        rows.append({"id": mid, "baseline": baseline, "mutant": mutant, "restored": restored})
        print(mid, baseline["exit"], mutant["exit"], restored["exit"], flush=True)

    Path(args.output).write_text(json.dumps({
        "schema": "r360-native-contract-mutations/1",
        "scope": args.only, "rows": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
