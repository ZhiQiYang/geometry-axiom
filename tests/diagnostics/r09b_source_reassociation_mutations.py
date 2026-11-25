"""R461 R3 v2 author source-mutated-module controls over the real native producer.

This is not the official native mutation ledger or a formal ME run. Each
withdrawal imports one altered product source file under its real module name
in a fresh Python process, then runs the unchanged unittest method. The product
file, test source, native binaries, and evidence ledgers are never rewritten.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "geometry-web" / "source_reassociation.py"
TEST = ROOT / "tests" / "test_r09b_source_reassociation.py"
ORACLE = ROOT / "tests" / "oracles" / "r09b_source_reassociation.py"
K3 = ROOT / "geometry-web" / "identity-ledger.js"
PREFIX = "tests.test_r09b_source_reassociation.SourceReassociation."

# (name, exact unique source anchor, withdrawn source, test method, assertion)
MUTATIONS = (('R09B_V2_MARK_CONTINUITY',
  'elif marker == root["incarnation"]:',
  'elif True:',
  'test_05_equal_geometry_new_mark_never_rewrites_old_replaced_fact',
  'R09B_V2_MARK_BEATS_EQUAL_GEOMETRY'),
 ('R09B_V2_CONFLICT_PRECEDENCE',
  'any(other != key and type(value) is dict and value.get("incarnation") == root["incarnation"]',
  'any(False and other != key and type(value) is dict and value.get("incarnation") == root["incarnation"]',
  'test_06_legal_world_conflict_allows_manual_draft_without_repairing_marks',
  'R09B_V2_CONFLICT_DIAGNOSTIC_RETAINED'),
 ('R09B_V2_CONTINUOUS_SCOPE',
  'if judgment["status"] == "continuous" and choice["placement_id"] != use["placement_id"]:',
  'if False:',
  'test_09_continuous_other_target_requires_later_carrier_edit',
  'R09B_V2_CONTINUOUS_RETARGET_OUTSIDE_D1'),
 ('R09B_V2_ORIENTATION',
  'type(choice["orientation"]) is not int or choice["orientation"] != use["orientation"] or',
  'type(choice["orientation"]) is not int or',
  'test_10_fixed_order_orientation_purpose_count_and_duplicate_guards',
  'R09B_V2_FIXED_ROW_orientation'),
 ('R09B_V2_PURPOSE',
  'choice["purpose"] != use["purpose"]):',
  'False):',
  'test_10_fixed_order_orientation_purpose_count_and_duplicate_guards',
  'R09B_V2_FIXED_ROW_purpose'),
 ('R09B_V2_OLD_RAW_WITNESS',
  '"beforeRaw": record_raw.decode("utf-8"),',
  '"beforeRaw": canonical_bytes(record).decode("utf-8"),',
  'test_03_legacy_unknown_keeps_exact_before_raw_and_no_backfill',
  'R09B_V2_OLD_RECORD_WITNESS'),
 ('R09B_V2_NATIVE_FRAME',
  '"after": new_frames[choice["placement_id"]],',
  '"after": old_frames[old["placement_id"]],',
  'test_13_frames_are_native_and_complete_model_replays_single_source',
  'R09B_V2_NATIVE_OLD_AND_NEW_FRAMES'),
 ('R09B_V2_COMPLETE_VALIDATION',
  'if canonical_bytes(expected) != canonical_bytes(candidate):',
  'if False:',
  'test_14_revalidation_rejects_old_fact_witness_frame_and_capability_tampering',
  'R09B_V2_AUDIT_TAMPER_REJECT_beforeRaw'),
 ('R09B_V2_LABEL_BOUND',
  'if len(value.encode("utf-8")) > MAX_CARRIER_LABEL_BYTES:',
  'if False:',
  'test_17_provisional_labels_have_exact_unique_bounded_mapping',
  'R09B_V2_PROVISIONAL_LABEL_GUARD'))

BY_NAME = {item[0]: item for item in MUTATIONS}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def variant(raw, mutation, withdrawn):
    source = raw.decode("utf-8").replace("\r\n", "\n")
    name, before, after, _, _ = mutation
    if source.count(before) != 1:
        raise AssertionError((name, "exact source anchor must occur once", source.count(before)))
    proposed = source.replace(before, after, 1) if withdrawn else source
    compile(proposed, str(PRODUCT), "exec")
    return proposed.encode("utf-8")


def child(args):
    """Load actual altered product bytes, not a replacement test double."""
    original = PRODUCT.read_bytes()
    if sha(original) != args.expect_source_sha or sha(TEST.read_bytes()) != args.expect_test_sha:
        raise AssertionError("R09B_MUTATION_SOURCE_CHANGED_DURING_RUN")
    mutation = BY_NAME[args.case]
    source = variant(original, mutation, args.phase == "withdrawal")
    for directory in (ROOT, ROOT / "geometry-core", ROOT / "geometry-web"):
        sys.path.insert(0, str(directory))
    with tempfile.TemporaryDirectory(prefix="r09b-product-withdrawal-") as directory:
        path = Path(directory) / "source_reassociation.py"
        path.write_bytes(source)
        spec = importlib.util.spec_from_file_location("source_reassociation", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        if module.LOADED_SHA != sha(source) or module.MODULE_PATH.read_bytes() != source:
            raise AssertionError("R09B_MUTATION_ACTUAL_LOADED_BYTES")
        print(json.dumps({"kind": "author-source-mutated-module", "case": args.case,
                          "phase": args.phase, "loaded_source_sha256": module.LOADED_SHA,
                          "disk_variant_sha256": sha(path.read_bytes()),
                          "original_product_sha256": sha(original), "test_sha256": args.expect_test_sha},
                         sort_keys=True), flush=True)
        unittest.main(module=None, argv=[str(Path(__file__)), "-v", PREFIX + mutation[3]])


def save_bytes(path, raw):
    path.write_bytes(raw)
    return {"file": path.name, "bytes": len(raw), "sha256": sha(raw)}


def validate_run(record, output, mutation, phase):
    name, _, _, method, marker = mutation
    if record["exit_code"] != (1 if phase == "withdrawal" else 0):
        raise AssertionError((name, phase, "unexpected exit", record["exit_code"]))
    if not re.search(r"Ran 1 test in [0-9.]+s\n", output):
        raise AssertionError((name, phase, "the requested real unittest did not run exactly once"))
    if method not in output or re.search(r"\nERROR:|\bskipped\b|\bSkipTest\b", output):
        raise AssertionError((name, phase, "error/skip is not behavioral evidence"))
    if phase == "withdrawal":
        if ("AssertionError:" not in output or marker not in output or
                not re.search(r"FAILED \(failures=[1-9][0-9]*\)\n", output)):
            raise AssertionError((name, "withdrawal did not reach its named behavioral assertion", marker))
        forbidden = ("TimeoutExpired", "BASE_TIMEOUT", "bridge closed", "R09B_NATIVE_ENVIRONMENT",
                     "ModuleNotFoundError", "ImportError", "SyntaxError")
        if any(word in output for word in forbidden):
            raise AssertionError((name, "environment/import/timeout does not count as a killed mutant"))
    elif "\nOK\n" not in output:
        raise AssertionError((name, phase, "baseline/restoration was not green"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bridge", default=os.environ.get("GEOMETRY_TEST_BRIDGE"))
    parser.add_argument("--base", default=os.environ.get("GEOMETRY_MODEL_BASE"))
    parser.add_argument("--case", choices=tuple(BY_NAME))
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--phase", choices=("baseline", "withdrawal", "restore"), help=argparse.SUPPRESS)
    parser.add_argument("--expect-source-sha", help=argparse.SUPPRESS)
    parser.add_argument("--expect-test-sha", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.child:
        if not all((args.case, args.phase, args.expect_source_sha, args.expect_test_sha)):
            parser.error("child requires exact case/phase/source/test")
        return child(args)
    if args.output is None or not args.bridge or not args.base:
        parser.error("--output plus explicit --bridge/--base (or their environment variables) are required")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    original = PRODUCT.read_bytes()
    test_bytes = TEST.read_bytes()
    oracle_bytes, k3_bytes = ORACLE.read_bytes(), K3.read_bytes()
    product_sha, test_sha = sha(original), sha(test_bytes)
    chosen = [BY_NAME[args.case]] if args.case else list(MUTATIONS)
    for mutation in chosen:
        variant(original, mutation, True)
    summary = {
        "schema": "r09b-author-source-module-withdrawals/2", "official_native_ledger": False,
        "execution": "fresh subprocess; actual variant file imported under canonical module name; unchanged unittest",
        "product": {"path": str(PRODUCT.relative_to(ROOT)), "bytes": len(original), "sha256": product_sha},
        "test": {"path": str(TEST.relative_to(ROOT)), "bytes": len(test_bytes), "sha256": test_sha},
        "oracle": {"path": str(ORACLE.relative_to(ROOT)), "bytes": len(oracle_bytes), "sha256": sha(oracle_bytes)},
        "existing_k3": {"path": str(K3.relative_to(ROOT)), "bytes": len(k3_bytes), "sha256": sha(k3_bytes)},
        "native": {"bridge": str(Path(args.bridge).resolve()), "base": str(Path(args.base).resolve()),
                   "bridge_sha256": sha(Path(args.bridge).read_bytes()), "base_sha256": sha(Path(args.base).read_bytes())},
        "original_source": save_bytes(output / "original-source.py", original),
        "mutations": [], "completed": False,
    }
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                   "GEOMETRY_TEST_BRIDGE": summary["native"]["bridge"],
                   "GEOMETRY_MODEL_BASE": summary["native"]["base"]}
    receipt_path = output / "results.json"

    def receipt():
        receipt_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8", newline="\n")

    receipt()
    for mutation in chosen:
        name, before, after, method, marker = mutation
        normalized = original.decode("utf-8").replace("\r\n", "\n").encode("utf-8")
        anchor = before.encode("utf-8")
        replacement = after.encode("utf-8")
        offset = normalized.index(anchor)
        row = {"name": name, "method": PREFIX + method, "assertion": marker,
               "anchor": before, "withdrawal": after,
               "anchor_metadata": {"matches": normalized.count(anchor), "byte_offset": offset,
                   "line": normalized[:offset].count(b"\n") + 1, "bytes": len(anchor), "sha256": sha(anchor)},
               "withdrawal_metadata": {"bytes": len(replacement), "sha256": sha(replacement)},
               "mutated_source": save_bytes(output / (name + ".py"), variant(original, mutation, True)),
               "runs": []}
        summary["mutations"].append(row)
        for phase in ("baseline", "withdrawal", "restore"):
            if (PRODUCT.read_bytes() != original or TEST.read_bytes() != test_bytes or
                    ORACLE.read_bytes() != oracle_bytes or K3.read_bytes() != k3_bytes):
                raise AssertionError("R09B_MUTATION_SOURCE_CHANGED_DURING_RUN")
            command = [sys.executable, "-B", str(Path(__file__).resolve()), "--child", "--case", name,
                       "--phase", phase, "--expect-source-sha", product_sha, "--expect-test-sha", test_sha]
            started = time.monotonic()
            result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=300)
            elapsed = time.monotonic() - started
            stem = name + "-" + phase
            run = {"phase": phase, "command": command, "exit_code": result.returncode,
                   "seconds": elapsed, "stdout": save_bytes(output / (stem + ".stdout"), result.stdout),
                   "stderr": save_bytes(output / (stem + ".stderr"), result.stderr)}
            save_bytes(output / (stem + ".exit"), (str(result.returncode) + "\n").encode("ascii"))
            row["runs"].append(run)
            receipt()
            validate_run(run, (result.stdout + result.stderr).decode("utf-8"), mutation, phase)
            if (PRODUCT.read_bytes() != original or TEST.read_bytes() != test_bytes or
                    ORACLE.read_bytes() != oracle_bytes or K3.read_bytes() != k3_bytes):
                raise AssertionError("R09B_MUTATION_SOURCE_CHANGED_DURING_RUN")
        row["exits"] = [run["exit_code"] for run in row["runs"]]
        if row["exits"] != [0, 1, 0]:
            raise AssertionError((name, row["exits"]))
        row["killed_and_restored"] = True
        receipt()
        print(name + " 0/1/0", flush=True)
    summary["completed"] = True
    summary["product_unchanged"] = PRODUCT.read_bytes() == original
    summary["test_unchanged"] = TEST.read_bytes() == test_bytes
    receipt()
    print("all author source-mutated-module controls killed and restored", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
