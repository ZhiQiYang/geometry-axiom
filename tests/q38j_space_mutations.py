"""Q38j-a isolated source mutations with named assertion-only verdicts.

Usage: GEOMETRY_MODEL_BASE=/fresh/model-base python tests/q38j_space_mutations.py --out /tmp/new-receipt-directory
Each selected test runs baseline, source variant and restored in fresh Python
processes. The source tree is never patched. Errors, skips, crashes, timeouts,
unexpected assertions and surviving mutants cannot count as kills.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
SM = "geometry-web/space_modeling.py"
SCENARIO = "geometry-web/scenario_verify.py"
UPDATE = "geometry-web/model_update.py"
JUDGE = "tests/test_space_profile_runs.py"
CALL = '    profile_runs = _profile_runs(data["profile_runs"], base, options) if "profile_runs" in data else None'
CASES = [
    ("Q38JA01-remove-profile-producer", SM, CALL, '    profile_runs = None',
     "test_q01_exact_native_members_reference_and_material_summary", "Q38JA_IMPLEMENTATION"),
    ("Q38JA02-count-envelope-as-material", SM,
     'profile_material_volume_mm3=str(sum(int(obj["section_profile"]["material_volume_mm3"]) for obj in members))',
     'profile_material_volume_mm3=str(sum(int(obj["volume_mm3"]) for obj in profile_runs["derived"]["objects"]))',
     "test_q01_exact_native_members_reference_and_material_summary", "Q38JA_MATERIAL"),
    ("Q38JA03-claim-overlap-checked", SM, 'profile_overlap_checked=False)', 'profile_overlap_checked=True)',
     "test_q01b_all_selected_roots_are_sorted_in_one_request", "Q38JA_OVERLAP"),
    ("Q38JA04-remove-unlocated-selection-guard", SM, 'if run.get("coordinate_space") != "world":', 'if False:',
     "test_q03_unlocated_member_has_d39_path_and_no_partial_result", "Q38JA_LOCAL"),
    ("Q38JA05-reject-zero-as-empty-id", SM,
     'if ref["kind"] != "profile-run" or type(identifier) is not int or not 0 <= identifier <= 0xFFFFFFFF:',
     'if ref["kind"] != "profile-run" or not identifier or type(identifier) is not int or not 0 <= identifier <= 0xFFFFFFFF:',
     "test_q04_zero_id_is_an_explicit_native_root", "Q38JA_ZERO_ID"),
    ("Q38JA06-swallow-selected-native-failure", SM, CALL,
     '    try:\n' + '    ' + CALL + '\n    except ModelError:\n        profile_runs = None',
     "test_q05_native_failure_preserves_status_diagnostic_and_rejects_whole_preview", "Q38JA_ALL_OR_NONE"),
    ("Q38JA07-remove-envelope-material-guard", SM,
     'details.get("dimensions_mm") is not None or details.get("material_volume_mm3") != "0"):',
     'details.get("dimensions_mm") is not None):',
     "test_q08_envelope_must_be_one_zero_material_reference_per_run", "Q38JA_ENVELOPE_GUARD"),
    ("Q38JA08-allow-missing-native-member", SM,
     'if any(envelopes[ref["id"]] != 1 or members[ref["id"]] !=',
     'if any(envelopes[ref["id"]] != 1 or False and members[ref["id"]] !=',
     "test_q08_missing_member_is_never_partial_success", "Q38JA_MEMBER_CLOSURE"),
    ("Q38JA09-remove-model-profile-replay", SM,
     'for key in ("space", "volume", "clearance", "walls", "timbers", "profile_runs"):',
     'for key in ("space", "volume", "clearance", "walls", "timbers"):',
     "test_q08_model_replay_validates_original_profile_manifest", "Q38JA_REPLAY_PROVENANCE"),
    ("Q38JA10-remove-independent-scenario-profile-replay", SCENARIO,
     '*(("profile_runs",) if "profile_runs" in inputs else ())', '*()',
     "test_q08f_scenario_replay_rejects_self_consistent_foreign_profile_package", "Q38JA_SCENARIO_PROFILE_REPLAY"),
    ("Q38JA11-skip-schema3-timber-replay", SCENARIO,
     '*(("timbers",) if "timbers" in inputs else ())', '*(("timbers",) if saved["schema"] == "geometry-space-preview/2" else ())',
     "test_q08f_schema3_scenario_still_verifies_original_timber_package", "Q38JA_SCENARIO_TIMBER_REPLAY"),
    ("Q38JC12-infer-omitted-profile-selection", UPDATE, 'def _selection(value):\n',
     'def _selection(value):\n    if type(value) is dict:\n        value.setdefault("profile_runs", [])\n',
     "test_q21c_f1b_requires_explicit_profile_selection", "Q38JC_EXPLICIT_SELECTION"),
    ("Q38JA13-mix-profile-and-space-volume", SM,
     '    if profile_runs is not None:\n        result.update(schema="geometry-space-preview/3", profile_runs=profile_runs)',
     '    if profile_runs is not None:\n        summary["volume_mm3"] = str(int(summary["volume_mm3"]) + 6415200)\n        result.update(schema="geometry-space-preview/3", profile_runs=profile_runs)',
     "test_q02_q17_omitted_selection_keeps_schema1_and_existing_packages_exact", "Q38JA_NO_CROSS_TOTAL"),
]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


class AssertionResult(unittest.TextTestResult):
    """Capture terminal exception values, independently of formatted traces."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failure_details = []

    def capture_failure(self, test, error):
        exception = error[1]
        self.failure_details.append({"test": test.id(),
                                     "exception_type": type(exception).__module__ + "." + type(exception).__qualname__,
                                     "message": str(exception)})

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.capture_failure(test, error)

    def addSubTest(self, test, subtest, error):
        super().addSubTest(test, subtest, error)
        if error is not None and issubclass(error[0], test.failureException):
            self.capture_failure(subtest, error)


def child(source, target, test, receipt):
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "geometry-web"))
    import start_local
    if sys.platform.startswith("linux"):
        start_local.ensure_stack()
    if source != "-":
        name = Path(target).stem
        module = types.ModuleType(name)
        module.__file__ = str(ROOT / target)
        sys.modules[name] = module
        # Preserve relative product lookup while executing exact variant bytes.
        exec(compile(Path(source).read_bytes(), module.__file__, "exec"), module.__dict__)
    from tests import test_space_profile_runs as judge
    suite = unittest.defaultTestLoader.loadTestsFromName(test, judge.SpaceProfileRuns)
    result = unittest.TextTestRunner(verbosity=2, resultclass=AssertionResult).run(suite)
    write_json(Path(receipt), {"run": result.testsRun, "failures": len(result.failures),
                              "errors": len(result.errors), "skipped": len(result.skipped),
                              "failure_details": result.failure_details,
                              "failure_text": [trace for _, trace in result.failures],
                              "error_text": [trace for _, trace in result.errors]})
    return 0 if result.wasSuccessful() else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--case", action="append", help="Run named cases only (repeatable).")
    args = parser.parse_args()
    selected = [case for case in CASES if not args.case or case[0] in args.case]
    if not selected or args.case and set(args.case) - {case[0] for case in CASES}:
        parser.error("Unknown or empty mutation selection")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(ROOT / "geometry-web"))
    import start_local
    if sys.platform.startswith("linux"):
        start_local.ensure_stack()
    source_paths = [SM, SCENARIO, UPDATE, JUDGE, "tests/q38j_space_mutations.py",
                    "tests/test_section_profile_modeling.py", "tests/binaries.py", "geometry-web/start_local.py"]
    original = {path: (ROOT / path).read_bytes() for path in source_paths}
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    binary = Path(os.environ["GEOMETRY_MODEL_BASE"])
    common = {"base_sha": base, "sources_sha256": {path: sha(data) for path, data in original.items()},
              "model_base": str(binary), "model_base_sha256": sha(binary.read_bytes()),
              "model_base_fingerprint_sha256": sha(Path(str(binary) + ".fingerprint.json").read_bytes())}
    write_json(out / "inputs.json", common)
    results = []
    for ident, target, before, after, test, marker in selected:
        directory = out / ident
        directory.mkdir()
        raw = original[target]
        newline = b"\r\n" if b"\r\n" in raw else b"\n"
        old = before.encode().replace(b"\n", newline)
        new = after.encode().replace(b"\n", newline)
        if raw.count(old) != 1:
            raise RuntimeError(ident + ": mutation anchor must occur exactly once")
        mutated = raw.replace(old, new)
        compile(mutated, str(ROOT / target), "exec")
        variant = directory / Path(target).name
        variant.write_bytes(mutated)
        phases = {}
        for phase in ("baseline", "mutant", "restored"):
            counts_path = directory / (phase + ".counts.json")
            command = [sys.executable, str(Path(__file__).resolve()), "--child",
                       str(variant) if phase == "mutant" else "-", target, test, str(counts_path)]
            started = time.monotonic()
            timed_out = False
            with (directory / (phase + ".stdout")).open("wb") as stdout, (directory / (phase + ".stderr")).open("wb") as stderr:
                try:
                    run = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr, timeout=120)
                    code = run.returncode
                except subprocess.TimeoutExpired:
                    timed_out = True
                    code = None
            counts = json.loads(counts_path.read_text()) if counts_path.exists() else None
            phase_receipt = {"base_sha": base, "command": command, "cwd": str(ROOT), "exit": code,
                             "seconds": time.monotonic() - started, "timeout": timed_out, "counts": counts,
                             "stdout_sha256": sha((directory / (phase + ".stdout")).read_bytes()),
                             "stderr_sha256": sha((directory / (phase + ".stderr")).read_bytes())}
            write_json(directory / (phase + ".execution.json"), phase_receipt)
            phases[phase] = phase_receipt
        def green(phase):
            item = phases[phase]
            return item["exit"] == 0 and item["counts"] == {"run": 1, "failures": 0, "errors": 0, "skipped": 0,
                                                          "failure_details": [], "failure_text": [], "error_text": []}
        red = phases["mutant"]
        counts = red["counts"]
        # A subTest may produce several designated assertion failures in the
        # same named test. Every failure must name this case's semantic oracle.
        killed = (green("baseline") and green("restored") and red["exit"] == 1 and not red["timeout"] and
                  counts is not None and counts["run"] == 1 and counts["failures"] > 0 and
                  counts["errors"] == counts["skipped"] == 0 and
                  len(counts["failure_details"]) == counts["failures"] and
                  all(detail["exception_type"] == "builtins.AssertionError" and marker in detail["message"]
                      for detail in counts["failure_details"]))
        unchanged = all((ROOT / path).read_bytes() == data for path, data in original.items())
        row = {"id": ident, "target": target, "test": test, "marker": marker,
               "source_sha256": sha(raw), "mutant_sha256": sha(mutated), "judge_sha256": sha(original[JUDGE]),
               "verdict": "killed" if killed and unchanged else "invalid", "source_unchanged": unchanged,
               "phases": phases}
        write_json(directory / "result.json", row)
        results.append(row)
        print(ident + ": " + row["verdict"], flush=True)
        write_json(out / "results.json", {**common, "cases": results,
                                          "killed": sum(r["verdict"] == "killed" for r in results), "total": len(selected)})
    return 0 if all(row["verdict"] == "killed" for row in results) else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        raise SystemExit(child(*sys.argv[2:]))
    raise SystemExit(main())
