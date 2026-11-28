#!/usr/bin/env python3
"""Withdraw actual independent-checker source bytes and retain raw 0/1/0 evidence.

No constructor hook or modified fixture is counted as a source withdrawal.
The repository source stays untouched; each subprocess compiles the exact
preserved original, changed, or restored file selected by R03B_CHECKER_SOURCE.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "tests/diagnostics/r03_notch_oracle.py"
JUDGE = ROOT / "tests/test_r03_notch_checker.py"
MUTATIONS = (
    ("R03B_CHECKER_SOURCE_WITHDRAW_TRUE_RC_SPAN",
     "        if valid_span is None:\n", "        if valid_span is None and False:\n",
     "test_C01_indoor_fake_boundary_cannot_terminate_main", "R03B_CHECKER_INDOOR_FAKE_BOUNDARY"),
    ("R03B_CHECKER_SOURCE_WITHDRAW_REQUIRED_MAIN",
     '            failures.append(dict(check="R03B_REQUIRED_MAIN_RC_SPAN", seam=seam, interval=[lo, hi]))\n',
     '            pass  # source withdrawal: required continuous main omitted\n',
     "test_C02_any_member_kind_cannot_replace_required_main", "R03B_CHECKER_REQUIRED_MAIN_KIND"),
    ("R03B_CHECKER_SOURCE_WITHDRAW_INPUT_SEAMS",
     "    if not seams_match:\n", "    if False:  # source withdrawal: trust candidate seams\n",
     "test_C03_deleted_seam_metadata_does_not_delete_obligation", "R03B_CHECKER_SEAMS_A_INDEPENDENT"),
    ("R03B_CHECKER_SOURCE_WITHDRAW_INPUT_AXES",
     '    if (result.get("a"), result.get("b")) != (derived["a"], derived["b"]):\n',
     '    if False:  # source withdrawal: trust candidate axes\n',
     "test_C05_candidate_axes_and_layout_are_not_input", "R03B_CHECKER_AXES_INDEPENDENT"),
    ("R03B_CHECKER_SOURCE_WITHDRAW_R42_COMPONENTS",
     "            components = material_components(occupied)\n", "            components = [occupied]\n",
     "test_C06_u_cut_splits_one_nominal_board_into_two_components", "R03B_CHECKER_R42_TWO_COMPONENTS"),
    ("R03B_CHECKER_SOURCE_WITHDRAW_TRANSVERSE_X",
     '            if segment["material_width"] < params["X"]:\n',
     '            if False:  # source withdrawal: waive transverse X\n',
     "test_C13_short_edge_exception_does_not_waive_transverse_bearing", "R03B_CHECKER_X_IS_NOT_TRANSVERSELY_WAIVED"),
)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def execute(directory, source, test):
    directory.mkdir(parents=True, exist_ok=True)
    source_path = directory / "r03_notch_oracle.py"
    source_path.write_bytes(source)
    command = [sys.executable, "-B", str(JUDGE), "-v", "NotchCheckerRegression." + test]
    environment = dict(os.environ, R03B_CHECKER_SOURCE=str(source_path))
    started = time.monotonic()
    process = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=60)
    (directory / "stdout.txt").write_bytes(process.stdout)
    (directory / "stderr.txt").write_bytes(process.stderr)
    receipt = dict(command=command, cwd=str(ROOT), exit=process.returncode,
                   source_file=str(source_path), source_bytes=len(source), source_sha256=sha(source),
                   judge_sha256=sha(JUDGE.read_bytes()), elapsed_seconds=time.monotonic() - started,
                   stdout_sha256=sha(process.stdout), stderr_sha256=sha(process.stderr))
    (directory / "execution.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt, process.stdout + process.stderr


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    original = CHECKER.read_bytes()
    records = []
    for name, before, after, test, exact_assertion in MUTATIONS:
        needle, replacement = before.encode(), after.encode()
        assert original.count(needle) == 1, "R03B_CHECKER_SOURCE_EXACT_ANCHOR: " + name
        withdrawn = original.replace(needle, replacement, 1)
        assert withdrawn != original, "R03B_CHECKER_SOURCE_BYTES_CHANGED: " + name
        steps = []
        for phase, source in (("baseline", original), ("withdrawn", withdrawn), ("restored", original)):
            receipt, raw = execute(output / name / phase, source, test)
            if phase == "withdrawn":
                assert receipt["exit"] == 1 and b"AssertionError" in raw and exact_assertion.encode() in raw, (
                    "R03B_CHECKER_SOURCE_EXACT_ASSERTION: " + name + " " + raw.decode(errors="replace"))
            else:
                assert receipt["exit"] == 0, "R03B_CHECKER_SOURCE_BASELINE_RESTORED: " + name + " " + raw.decode(errors="replace")
            steps.append(receipt)
        exits = [step["exit"] for step in steps]
        assert exits == [0, 1, 0], "R03B_CHECKER_SOURCE_TRIPLET: " + name
        records.append(dict(name=name, kind="independent-checker-source-withdrawal", exits=exits,
                            exact_assertion=exact_assertion, phases=steps))
        print(json.dumps(dict(name=name, exits=exits, exact_assertion=exact_assertion)), flush=True)
    assert CHECKER.read_bytes() == original, "R03B_CHECKER_SOURCE_REPOSITORY_UNCHANGED"
    receipt = dict(schema="r03-notch-checker-source-withdrawals/1", source_sha256=sha(original),
                   judge_sha256=sha(JUDGE.read_bytes()), counts=dict(killed=len(records), blocked=0), records=records)
    (output / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(output=str(output), counts=receipt["counts"])))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    output = args.out if args.out is not None else Path(tempfile.mkdtemp(prefix="r03b-checker-source-"))
    return run(output.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
