"""Q38j-c isolated F1b source mutations with named assertion-only verdicts.

Usage: GEOMETRY_MODEL_BASE=/fresh/model-base GEOMETRY_TEST_BRIDGE=/fresh/bridge
       python tests/q38j_update_mutations.py --out /tmp/new-receipt-directory
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
JUDGE = "tests/test_space_profile_update.py"
WRITE_PROFILE = '        if selection["profile_runs"]:\n            inputs["profile_runs"] = deepcopy(selection["profile_runs"])'
CANONICAL_BOUNDARY = ('    if (not face_mode and selected["boundary_id"] is None and\n'
                      '            (record["input"].get("profile_runs") or inputs.get("profile_runs") or record["source"]["boundary_id"] is None)):')
CASES = [
    ("R430_UPDATE_RAW_SOURCE_WITHDRAWAL", UPDATE,
     'inputs["base_scene"] = data["current_scene"]', 'inputs["base_scene"] = new_base["base_scene"]',
     "test_r430_update_preserves_the_selected_raw_source_and_native_canonical_receipt", "R430_UPDATE_RAW_SOURCE"),
    ("Q38JC01-remove-selected-profile-output", UPDATE, WRITE_PROFILE,
     '        if False:\n            inputs["profile_runs"] = deepcopy(selection["profile_runs"])',
     "test_q20_add_copied_run_rebuilds_every_package_from_one_current_source", "Q38JC_ADD"),
    ("Q38JC02-remove-fixed-profile-roots", UPDATE,
     '[*inputs["obstacles"], *inputs.get("timbers", []), *inputs.get("profile_runs", [])]',
     '[*inputs["obstacles"], *inputs.get("timbers", [])]',
     "test_q22_same_material_version_changed_content_is_rejected_from_profile_closure", "Q38JC_FIXED_PROFILE_VERSION"),
    ("Q38JC03-remove-profile-package-diff", UPDATE,
     'PACKAGES = ("space", "volume", "clearance", "walls", "timbers", "profile_runs")',
     'PACKAGES = ("space", "volume", "clearance", "walls", "timbers")',
     "test_q20_add_copied_run_rebuilds_every_package_from_one_current_source", "Q38JC_DIFF_PACKAGES"),
    ("Q38JC04-retain-old-profile-on-empty-selection", UPDATE, WRITE_PROFILE,
     '        if selection["profile_runs"] or record["input"].get("profile_runs"):\n            inputs["profile_runs"] = deepcopy(selection["profile_runs"] or record["input"]["profile_runs"])',
     "test_q21_explicit_empty_removes_profile_package_without_old_fallback", "Q38JC_REMOVE"),
    ("Q38JC05-splice-new-package-into-old-snapshot", UPDATE,
     '    result = space_modeling.preview(inputs, base_executable=base, max_cells=max_cells)',
     '    result = space_modeling.preview(inputs, base_executable=base, max_cells=max_cells)\n    inputs["base_scene"] = record["input"]["base_scene"]',
     "test_q20_add_copied_run_rebuilds_every_package_from_one_current_source", "Q38JC_FULL_SOURCE"),
    ("Q38JC06-skip-fixed-profile-field-associations", UPDATE,
     '    _fixed_associations(old_associations, new_associations)',
     '    # Mutant: silently accept swapped fixed material field references.',
     "test_q22_equal_value_A_B_fixed_reference_swap_is_rejected_per_member_field", "Q38JC_FIXED_PROFILE_FIELDS"),
    ("Q38JC07-drop-native-embedded-boundary", UPDATE, CANONICAL_BOUNDARY,
     '    if False:',
     "test_q20_embedded_profile_source_retains_native_null_boundary_for_all_replays", "Q38JC_EMBEDDED_BOUNDARY"),
    ("Q38JC08-repair-invalid-old-profile-boundary", UPDATE,
     '        if "profile_runs" in record["input"] and record["source"]["boundary_id"] != old_selected["boundary_id"]:',
     '        if False:',
     "test_q20_embedded_profile_source_retains_native_null_boundary_for_all_replays", "Q38JC_OLD_EMBEDDED_SOURCE"),
    ("Q38JC09-drop-embedded-boundary-after-profile-removal", UPDATE, CANONICAL_BOUNDARY,
     '    if inputs.get("profile_runs") and selected["boundary_id"] is None:',
     "test_q20_embedded_profile_source_retains_native_null_boundary_for_all_replays", "Q38JC_EMBEDDED_REMOVE"),
    ("Q38JC10-forget-canonical-embedded-boundary-on-next-update", UPDATE,
     ' or record["source"]["boundary_id"] is None', '',
     "test_q20_embedded_profile_source_retains_native_null_boundary_for_all_replays", "Q38JC_EMBEDDED_CONTINUATION"),
    ("Q38JK01-reject-legal-covered-identity-in-scenario", SCENARIO,
     '_keys(record, ("id", "name", "created_at", "source", "input", "result"), ("sourceIdentity",), path=path)',
     '_keys(record, ("id", "name", "created_at", "source", "input", "result"), path=path)',
     "test_qk03_covered_identity_and_profile_model_use_same_strict_replay_roots", "Q38JK_COVERED_REPLAY"),
    ("Q38JK02-accept-fabricated-profile-pin-in-scenario", SCENARIO,
     '        validate_model_source_identity(record)', '        pass  # Mutant: accepts unverified identity roots.',
     "test_qk02_profile_pin_or_uncovered_reason_never_enters_covered_identity", "Q38JK_SCENARIO_PROFILE_PIN"),
    ("Q38JK03-drop-covered-root-completeness", UPDATE,
     '    if sorted(found) != sorted(expected):', '    if False:',
     "test_qk03_original_covered_pins_cannot_be_dropped_because_runs_are_untracked", "Q38JK_COVERED_ROOTS"),
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
    from tests import test_space_profile_update as judge
    suite = unittest.defaultTestLoader.loadTestsFromName(test, judge.SpaceProfileUpdate)
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
    source_paths = [SM, SCENARIO, UPDATE, JUDGE, "tests/q38j_update_mutations.py", "tests/q38j_space_mutations.py", "tests/test_space_profile_runs.py",
                    "tests/_bridge.py",
                    "tests/test_section_profile_modeling.py", "tests/binaries.py", "geometry-web/start_local.py"]
    original = {path: (ROOT / path).read_bytes() for path in source_paths}
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    binary = Path(os.environ["GEOMETRY_MODEL_BASE"])
    bridge = Path(os.environ["GEOMETRY_TEST_BRIDGE"])
    common = {"base_sha": base, "sources_sha256": {path: sha(data) for path, data in original.items()},
              "bridge": str(bridge), "bridge_sha256": sha(bridge.read_bytes()),
              "bridge_fingerprint_sha256": sha(Path(str(bridge) + ".fingerprint.json").read_bytes()),
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
