"""Bounded named 0/1/0 withdrawals for R09b D2/S1.

This diagnostic loads copies of the actual product source in fresh processes.
It never edits repository files, adjusts existing tests, or counts timeouts,
imports, skips or unrelated assertions as the expected red.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "geometry-web" / "model_carrier_edit.py"
TIMEOUT_SECONDS = 120

MUTATIONS = (
    ("D2_INDEX_INSTEAD_OF_CARRIER", "CarrierSelection.test_04_reorder_keeps_orientation_and_purpose_on_carrier",
     "R09B_D2_SETTINGS_FOLLOW_CARRIER",
     'old_index, old = old_by_label.get(label, (None, None))',
     'old_index, old = index, old_uses[index]'),
    ("D2_ALLOW_DUPLICATE_TARGET", "CarrierSelection.test_05_empty_duplicate_and_incomplete_new_rows_are_refused",
     "R09B_D2_EXPLICIT_UNIQUE_NONEMPTY_LIST",
     'if target in targets:', 'if False and target in targets:'),
    ("D2_LOSE_RETAINED_SETTINGS", "CarrierSelection.test_06_retained_settings_cannot_silently_change",
     "R09B_D2_RETAINED_SETTINGS_PINNED",
     'if operation == "retained" and (choice["orientation"] != old["orientation"] or',
     'if False and operation == "retained" and (choice["orientation"] != old["orientation"] or'),
    ("D2_DROP_FIXED_VERSION", "NativeCarrierEdit.test_21_fixed_versions_follow_each_carrier_not_global_union",
     "R09B_D2_FIXED_VERSION_PER_CARRIER",
     'model_update._fixed_versions(old_fixed, new_fixed)', 'pass  # withdrawn fixed-version comparison'),
    ("D2_DROP_FIXED_ASSOCIATION", "NativeCarrierEdit.test_22_fixed_field_associations_cannot_swap_while_union_matches",
     "R09B_D2_FIXED_ASSOCIATION_PER_CARRIER",
     'model_update._fixed_associations(old_paths, new_paths)', 'pass  # withdrawn fixed-association comparison'),
    ("D2_TRUST_CANDIDATE_SELECTION", "NativeCarrierEdit.test_13_external_original_selection_rejects_other_self_consistent_candidate",
     "R09B_D2_EXTERNAL_SELECTION_BOUND",
     'expected = prepare_candidate(record_raw, source_scene, selection, project_id=project_id,',
     'expected = prepare_candidate(record_raw, source_scene, candidate["selection"], project_id=project_id,'),
    ("D2_REWRITE_OLD_BYTE_WITNESS", "NativeCarrierEdit.test_08_unknown_inactive_keeps_no_mark_and_exact_old_bytes",
     "R09B_D2_EXACT_OLD_BYTES",
     '"beforeRaw": record_raw.decode("utf-8"),', '"beforeRaw": canonical_bytes(record).decode("utf-8"),'),
    ("D2_REWRITE_OLD_REPLACED_FACT", "NativeCarrierEdit.test_06_replaced_same_geometry_preserves_old_fact_and_new_reference",
     "R09B_D2_OLD_REPLACED_FACT",
     '"comparison": [{"carrierId": label, **deepcopy(row)} for label, row in zip(carrier_ids, comparison)],',
     '"comparison": [{"carrierId": label, **deepcopy(row), "status": "continuous"} for label, row in zip(carrier_ids, comparison)],'),
    ("D2_IGNORE_SELECTED_ORIENTATION", "NativeCarrierEdit.test_04_continuous_retarget_rechecks_explicit_orientation_and_purpose",
     "R09B_D2_NEW_EFFECTIVE_NORMAL",
     '[new["orientation"] * value for value in after["n"]]', 'deepcopy(after["n"])'),
    ("D2_IGNORE_EARLY_RUNTIME", "NativeCarrierEdit.test_25_context_runtime_is_bound_before_old_replay_and_source_observation",
     "R09B_D2_CONTEXT_RUNTIME",
     'if context_runtime != {key: value for key, value in runtime.items() if key != "carrier_edit_sha256"}:',
     'if False and context_runtime != {key: value for key, value in runtime.items() if key != "carrier_edit_sha256"}:'),
)

RUNNER = r'''import importlib.util
import json
from pathlib import Path
import sys
import unittest
class ActualResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executed_ids = []
        self.actual_failures = []
    def startTest(self, test):
        self.executed_ids.append(test.id())
        super().startTest(test)
    def capture_failure(self, test, err):
        self.actual_failures.append({"id": test.id(),
            "exceptionType": err[0].__module__ + "." + err[0].__qualname__,
            "message": str(err[1])})
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.capture_failure(test, err)
    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None and issubclass(err[0], test.failureException):
            self.capture_failure(subtest, err)
root = Path(sys.argv[1])
for directory in (root, root / "geometry-core", root / "geometry-web"):
    sys.path.insert(0, str(directory))
spec = importlib.util.spec_from_file_location("model_carrier_edit", sys.argv[2])
module = importlib.util.module_from_spec(spec)
sys.modules["model_carrier_edit"] = module
spec.loader.exec_module(module)
suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_r09b_model_carrier_edit." + sys.argv[3])
result = unittest.TextTestRunner(verbosity=2, resultclass=ActualResult).run(suite)
if len(result.actual_failures) != len(result.failures) or any(
        actual["id"] != test.id() for actual, (test, _) in zip(result.actual_failures, result.failures)):
    raise RuntimeError("R09B_D2_DIAGNOSTIC_FAILURE_RECEIPT_MISMATCH")
receipt = {"run": result.testsRun, "tests": result.executed_ids,
           "failures": [{**actual, "traceback": trace}
                        for actual, (_, trace) in zip(result.actual_failures, result.failures)],
           "errors": [{"id": test.id(), "traceback": trace} for test, trace in result.errors],
           "skips": [{"id": test.id(), "reason": why} for test, why in result.skipped]}
print("R09B_D2_PROBE_RESULT " + json.dumps(receipt, ensure_ascii=False, sort_keys=True))
sys.exit(0 if result.wasSuccessful() and not result.skipped and result.testsRun == 1 else 1)
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(command, directory, environment):
    started = time.monotonic()
    child = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, start_new_session=os.name == "posix")
    timed_out = False
    try:
        stdout, stderr = child.communicate(timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == "posix":
            os.killpg(child.pid, signal.SIGKILL)
        else:
            child.kill()
        stdout, stderr = child.communicate(timeout=10)
    directory.mkdir(parents=True)
    (directory / "stdout.txt").write_bytes(stdout)
    (directory / "stderr.txt").write_bytes(stderr)
    (directory / "exit.txt").write_text(str(child.returncode) + "\n", encoding="ascii")
    (directory / "command.json").write_text(json.dumps(command, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    prefixes = [line[len(b"R09B_D2_PROBE_RESULT "):] for line in stdout.splitlines()
                if line.startswith(b"R09B_D2_PROBE_RESULT ")]
    receipt = None
    if len(prefixes) == 1:
        try:
            receipt = json.loads(prefixes[0])
        except (ValueError, UnicodeDecodeError):
            pass
    return {"command": command, "exit": child.returncode, "timeout": timed_out,
            "seconds": time.monotonic() - started, "receipt": receipt,
            "stdoutSha256": sha(stdout), "stderrSha256": sha(stderr)}


def check_run(execution, *, red, marker, test_id):
    record = execution.get("receipt")
    if (execution.get("timeout") is not False or not isinstance(record, dict)
            or type(record.get("run")) is not int or record["run"] != 1
            or record.get("tests") != [test_id]
            or record.get("errors") != [] or record.get("skips") != []
            or type(execution.get("exit")) is not int):
        return False
    failures = record.get("failures")
    if type(failures) is not list:
        return False
    if red:
        return (execution["exit"] == 1 and bool(failures)
                and all(type(failure) is dict
                    and (failure.get("id") == test_id or
                         type(failure.get("id")) is str and
                         failure["id"].startswith(test_id + " (") and failure["id"].endswith(")"))
                    and failure.get("exceptionType") == "builtins.AssertionError"
                    and type(failure.get("message")) is str and marker in failure["message"]
                    for failure in failures))
    return execution["exit"] == 0 and not failures


def guard_selftest():
    """Synthetic receipts exercise classification, not native-product behavior."""
    test_id, marker = "tests.probe.Case.test_target", "R09B_D2_EXPECTED_ASSERTION"
    green = {"timeout": False, "exit": 0, "receipt": {"run": 1, "tests": [test_id],
             "failures": [], "errors": [], "skips": []}}
    red = deepcopy(green)
    red["exit"] = 1
    red["receipt"]["failures"] = [{"id": test_id, "exceptionType": "builtins.AssertionError",
        "message": marker, "traceback": "source context contains AssertionError: " + marker}]
    examples = [("valid-green", green, False, True), ("valid-target-red", red, True, True)]
    subtest = deepcopy(red)
    subtest["receipt"]["failures"][0]["id"] += " (choice=1)"
    examples.append(("valid-target-subtest", subtest, True, True))
    changes = (
        ("wrong-executed-method", ("receipt", "tests"), [test_id + "_unrelated"]),
        ("wrong-failure-method", ("receipt", "failures", 0, "id"), test_id + "_unrelated"),
        ("non-assertion-with-marker-in-trace", ("receipt", "failures", 0, "exceptionType"), "builtins.ValueError"),
        ("unrelated-assertion-with-marker-in-trace", ("receipt", "failures", 0, "message"), "unrelated assertion"),
        ("error-is-blocked", ("receipt", "errors"), [{"id": test_id, "traceback": marker}]),
        ("skip-is-blocked", ("receipt", "skips"), [{"id": test_id, "reason": marker}]),
        ("timeout-is-blocked", ("timeout",), True),
        ("wrong-exit-is-blocked", ("exit",), 0),
    )
    for name, path, value in changes:
        example = deepcopy(red)
        target = example
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        examples.append((name, example, True, False))
    receipts = []
    for name, execution, is_red, expected in examples:
        observed = check_run(execution, red=is_red, marker=marker, test_id=test_id)
        if observed is not expected:
            raise AssertionError("R09B_D2_DIAGNOSTIC_FALSE_CLASSIFICATION: " + name)
        receipts.append({"name": name, "expectedAccepted": expected, "accepted": observed})
    return receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--bridge")
    parser.add_argument("--base")
    parser.add_argument("--only", choices=[item[0] for item in MUTATIONS])
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output == ROOT or ROOT in output.parents or output.exists():
        parser.error("output must be a new directory outside the checkout")
    original = PRODUCT.read_bytes()
    text = original.decode("utf-8")
    output.mkdir(parents=True)
    selftest = guard_selftest()
    (output / "guard-selftest.json").write_text(json.dumps(selftest, indent=2) + "\n", encoding="utf-8")
    (output / "runner.py").write_text(RUNNER, encoding="utf-8", newline="\n")
    environment = dict(os.environ)
    if args.bridge:
        environment["GEOMETRY_TEST_BRIDGE"] = str(Path(args.bridge).resolve())
    if args.base:
        environment["GEOMETRY_MODEL_BASE"] = str(Path(args.base).resolve())
    results = []
    definitions = [row for row in MUTATIONS if args.only is None or row[0] == args.only]
    for name, test, marker, before, after in definitions:
        if text.count(before) != 1:
            raise RuntimeError(name + ": mutation anchor must occur exactly once")
        directory = output / name
        directory.mkdir()
        changed = text.replace(before, after).encode("utf-8")
        product_files = []
        for phase, source in (("baseline", original), ("withdrawal", changed), ("restore", original)):
            path = directory / (phase + ".py")
            path.write_bytes(source)
            product_files.append((phase, path))
        row = {"name": name, "test": test, "marker": marker,
               "sourceSha256": sha(original), "withdrawalSha256": sha(changed), "executions": []}
        for phase, path in product_files:
            command = [sys.executable, "-B", str(output / "runner.py"), str(ROOT), str(path), test]
            execution = run(command, directory / phase, environment)
            execution["phase"] = phase
            row["executions"].append(execution)
        row["exits"] = [item["exit"] for item in row["executions"]]
        row["valid"] = all(check_run(item, red=item["phase"] == "withdrawal", marker=marker,
                                   test_id="tests.test_r09b_model_carrier_edit." + test)
                           for item in row["executions"])
        results.append(row)
        (output / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"name": name, "exits": row["exits"], "valid": row["valid"]}, sort_keys=True), flush=True)
    if PRODUCT.read_bytes() != original:
        raise RuntimeError("repository product source changed during diagnosis")
    return 0 if all(row["valid"] for row in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
