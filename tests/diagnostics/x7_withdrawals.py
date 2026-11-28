#!/usr/bin/env python3
"""Reproduce X7's named 0/1/0 controls without editing product files.

One ordinary observer binary and one isolated mutant binary per control are
compiled by the real X7 test builder. Every leg runs the original named test
method in a fresh process, with fresh raw artifacts and an exact binary hash.
An error, skip, crash, timeout or unrelated assertion is never a killed mutant.
This diagnostic report is not a Mutation evidence workflow receipt.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import difflib
import hashlib
import importlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time
import traceback
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests/diagnostics"))
import x7_benchmark as benchmark
import x7_scenarios as scenes

TARGET = "geometry-web/framing_template_bridge.inc"
SUCCESS = "test_01_room53_work_and_exact_bytes"
FAILURE = "test_03_first_error_and_scope_on_both_failure_phases"
WORK_MARKER = "X7_PREVIEW_FULL_VALIDATIONS_BOUNDED"
ERROR_MARKER = "X7_FAILURE_ORIGINAL_BYTES_STDERR_AND_ISSUES"


@dataclass(frozen=True)
class Withdrawal:
    name: str
    before: bytes
    after: bytes
    method: str
    marker: str


WITHDRAWALS = (
    Withdrawal("batch", b"    AppWorldCandidate *candidate=g_active_app_candidate;",
               b"    return framing_template_marks_stage(w,c,g_reference_validation_deferred);\n"
               b"    AppWorldCandidate *candidate=g_active_app_candidate;", SUCCESS, WORK_MARKER),
    Withdrawal("defer_restore", b"    g_reference_validation_deferred=previous_deferred;",
               b"    /* withdrawn: restore the marks deferred scope */", SUCCESS,
               "X7_DEFER_SCOPE_RESTORED"),
    Withdrawal("mute_attempt", b"    g_scene_error_muted=true; /* X7_MARKS_MUTED_ATTEMPT */",
               b"    /* withdrawn: mute the speculative marks attempt */", FAILURE, ERROR_MARKER),
    Withdrawal("world_rollback", b"    memcpy(w,checkpoint,sizeof *w); /* X7_MARKS_WORLD_ROLLBACK */",
               b"    /* withdrawn: restore the pre-mark World */", FAILURE, ERROR_MARKER),
    Withdrawal("issues_rollback", b"    g_reference_issue_count=issues_before; /* X7_MARKS_DIAGNOSTIC_RESTORE */",
               b"    /* withdrawn: restore the pre-mark issue count */", FAILURE, ERROR_MARKER),
    Withdrawal("batch_validation", b"    if(ok)ok=world_revalidate(w); /* X7_MARKS_COMPLETE_VALIDATION */",
               b"    /* withdrawn: validate the complete staged mark batch */", SUCCESS, WORK_MARKER),
    Withdrawal("fallback_replay", b"    return framing_template_marks_stage(w,c,previous_deferred); /* X7_MARKS_FALLBACK_REPLAY */",
               b"    return false; /* withdrawn: original-order failure replay */", FAILURE, ERROR_MARKER),
    Withdrawal("final_whole_validation", b"    if(ok)ok=world_revalidate(w); /* R03_COMPLETE_NATIVE_VALIDATION */",
               b"    /* withdrawn: validate the complete native R03 candidate */", SUCCESS,
               "X7_COMPLETE_NATIVE_PREVIEW_ACCEPTED"),
    Withdrawal("confirm_validation", b"    if(before==UINT64_MAX||!app_world_candidate_revalidate(g_preview.transaction,&g_world)){",
               b"    if(before==UINT64_MAX){", SUCCESS,
               "X7_CONFIRM_FULL_VALIDATION_RETAINED"),
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    scenes.write_json(path, value)


def artifact(path, root):
    return {"path": str(path.relative_to(root)), "bytes": path.stat().st_size,
            "sha256": digest(path)}


def source_manifest(directory):
    return [{"path": path.relative_to(directory).as_posix(),
             "bytes": path.stat().st_size, "sha256": digest(path)}
            for path in sorted(directory.rglob("*"))
            if path.is_file() and path.suffix in (".c", ".h", ".inc")]


class EvidenceResult(unittest.TextTestResult):
    """Keep structured exception identity as well as unmodified unittest text."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observations = []

    def observe(self, test, err, kind):
        self.observations.append({"test": str(test), "kind": kind,
                                  "exception": err[0].__module__ + "." + err[0].__name__,
                                  "message": str(err[1]),
                                  "x7_assertion": getattr(err[1], "x7_assertion", None),
                                  "traceback": [{"file": str(Path(frame.filename).resolve()),
                                                 "line": frame.lineno, "function": frame.name}
                                                for frame in traceback.extract_tb(err[2])],
                                  "bridge_closed": bool(getattr(err[1], "bridge_closed", False))})

    def addFailure(self, test, err):
        self.observe(test, err, "failure")
        super().addFailure(test, err)

    def addError(self, test, err):
        self.observe(test, err, "error")
        super().addError(test, err)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            kind = "failure" if issubclass(err[0], test.failureException) else "error"
            self.observe(subtest, err, kind)
        super().addSubTest(test, subtest, err)


def child(args):
    binary = args.binary.resolve()
    scenes.require(binary.is_file() and digest(binary) == args.binary_sha256,
                   "X7_WITHDRAWAL_EXACT_BINARY_BEFORE")
    scenes.require(digest(args.fixtures) == args.fixtures_sha256,
                   "X7_WITHDRAWAL_EXACT_FIXTURE_BUNDLE")
    # The regular test validates every referenced scene/geometry file itself.
    os.environ["GEOMETRY_X7_FIXTURES"] = str(args.fixtures.resolve())
    os.environ["GEOMETRY_X7_ARTIFACTS"] = str(args.artifacts.resolve())
    module = importlib.import_module("tests.test_x7_performance")

    def compiled_probe(out, mutate=None):
        scenes.require(mutate is None, "X7_CHILD_NO_SECOND_MUTATION")
        scenes.require(digest(binary) == args.binary_sha256,
                       "X7_WITHDRAWAL_EXACT_BINARY_AT_TEST_SETUP")
        out.mkdir(parents=True, exist_ok=False)
        write_json(out / "selected-probe.json", {"path": str(binary), "sha256": digest(binary)})
        return binary

    module.build_probe = compiled_probe
    suite = unittest.TestSuite([module.X7NativePerformance(args.method)])
    result = unittest.TextTestRunner(verbosity=2, resultclass=EvidenceResult).run(suite)
    binary_after = digest(binary)
    report = {"schema": "x7-withdrawal-child/1", "method": args.method,
              "binary": str(binary), "binary_sha256": args.binary_sha256,
              "binary_after_sha256": binary_after,
              "tests_run": result.testsRun, "failures": len(result.failures),
              "errors": len(result.errors), "skips": len(result.skipped),
              "unexpected_successes": len(result.unexpectedSuccesses),
              "expected_failures": len(result.expectedFailures),
              "observations": result.observations,
              "successful": result.wasSuccessful() and binary_after == args.binary_sha256}
    write_json(args.child_result, report)
    return 0 if report["successful"] else 1


def run_phase(args, out, name, phase, binary, binary_sha, method):
    directory = out / "runs" / name / phase
    directory.mkdir(parents=True, exist_ok=False)
    result_path = directory / "result.json"
    actual_binary_sha = digest(binary)
    scenes.require(actual_binary_sha == binary_sha, "X7_WITHDRAWAL_PINNED_BUILD_BINARY", name)
    command = [sys.executable, str(Path(__file__).resolve()), "--child",
               "--binary", str(binary), "--binary-sha256", binary_sha,
               "--fixtures", str(args.fixtures.resolve()), "--fixtures-sha256", digest(args.fixtures),
               "--artifacts", str(directory / "artifacts"), "--child-result", str(result_path),
               "--method", method]
    record = {"argv": command, "shell_display": shlex.join(command), "cwd": str(ROOT),
              "timeout_seconds": args.phase_timeout, "build_binary_sha256": binary_sha,
              "binary_sha256": actual_binary_sha,
              "timed_out": False}
    write_json(directory / "command.json", record)
    started = time.monotonic()
    with (directory / "stdout.txt").open("xb") as stdout, (directory / "stderr.txt").open("xb") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr,
                                   start_new_session=(os.name != "nt"))
        try:
            code = process.wait(timeout=args.phase_timeout)
        except subprocess.TimeoutExpired:
            record["timed_out"] = True
            if os.name != "nt":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.wait(timeout=10)
            code = 124
    record.update({"exit_code": code, "child_returncode": process.returncode,
                   "seconds": time.monotonic() - started,
                   "binary_after_sha256": digest(binary)})
    write_json(directory / "command.json", record)
    record["stdout"] = artifact(directory / "stdout.txt", out)
    record["stderr"] = artifact(directory / "stderr.txt", out)
    record["command"] = artifact(directory / "command.json", out)
    record["result"] = json.loads(result_path.read_bytes()) if result_path.is_file() else None
    record["result_file"] = artifact(result_path, out) if result_path.is_file() else None
    return record


def infrastructure_ok(record):
    result = record["result"]
    return (not record["timed_out"] and result is not None and result["tests_run"] == 1
            and result["errors"] == 0 and result["skips"] == 0
            and result["expected_failures"] == 0 and result["unexpected_successes"] == 0
            and record["build_binary_sha256"] == record["binary_sha256"] == record["binary_after_sha256"]
            == result["binary_sha256"] == result["binary_after_sha256"]
            and all(not row["bridge_closed"] for row in result["observations"]))


def is_green(record):
    return (infrastructure_ok(record) and record["exit_code"] == 0
            and record["result"]["successful"] and record["result"]["failures"] == 0)


def is_named_red(record, control):
    if not infrastructure_ok(record) or record["exit_code"] != 1:
        return False
    result = record["result"]
    test_file = str(ROOT / "tests/test_x7_performance.py")
    return (not result["successful"] and result["method"] == control.method and result["failures"] > 0
            and len(result["observations"]) == result["failures"]
            and all(row["kind"] == "failure" and row["exception"] == "builtins.AssertionError"
                    and row.get("x7_assertion") == control.marker
                    and any(frame["file"] == test_file and frame["function"] == control.method
                            for frame in row.get("traceback", []))
                    and any(frame["file"] == test_file and frame["function"] == "assert_contract"
                            for frame in row.get("traceback", []))
                    for row in result["observations"]))


def make_mutation(control, out, report):
    def mutate(directory):
        path = directory / TARGET
        original = path.read_bytes()
        scenes.require(original.count(control.before) == 1,
                       "X7_WITHDRAWAL_UNIQUE_PRODUCT_SITE", control.name)
        changed = original.replace(control.before, control.after)
        scenes.require(changed != original, "X7_WITHDRAWAL_CHANGES_PRODUCT", control.name)
        path.write_bytes(changed)
        patch = "".join(difflib.unified_diff(original.decode().splitlines(keepends=True),
                                           changed.decode().splitlines(keepends=True),
                                           fromfile="a/" + TARGET, tofile="b/" + TARGET))
        patch_path = out / "mutations" / (control.name + ".patch")
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_path.write_text(patch, encoding="utf-8")
        report.update({"file": TARGET, "matches": 1,
                       "before_sha256": hashlib.sha256(original).hexdigest(),
                       "after_sha256": hashlib.sha256(changed).hexdigest(),
                       "patch": artifact(patch_path, out)})
    return mutate


def build(module, directory, out, mutation=None, reuse=None, reuse_root=None):
    started = time.monotonic()
    reused = None
    if reuse is None:
        binary = module.build_probe(directory, mutation)
    else:
        module.prepare_probe(directory, mutation)
        prepared = source_manifest(directory)
        recorded = json.loads(scenes.read_file(reuse["sources"], reuse_root))
        scenes.require(prepared == recorded, "X7_REUSE_FULL_INSTRUMENTED_CLOSURE_IDENTICAL", str(directory))
        compile_bytes = scenes.read_file(reuse["compile"], reuse_root)
        compile_record = json.loads(compile_bytes)
        command = compile_record["argv"]
        old_binary = reuse_root / reuse["binary"]["path"]
        scenes.require(compile_record["exit_code"] == 0 and len(command) == 7
                       and command[1:3] == ["-std=c11", "-O2"] and command[4:6] == ["-lm", "-o"]
                       and Path(command[3]) == old_binary.parent / "geometry-web/web_bridge.c"
                       and Path(command[6]) == old_binary, "X7_REUSE_EXACT_SUCCESSFUL_COMPILE_COMMAND")
        binary = directory / "x7-probe-bridge"
        binary.write_bytes(scenes.read_file(reuse["binary"], reuse_root))
        binary.chmod(0o700)
        (directory / "compile.json").write_bytes(compile_bytes)
        (directory / "compile.stdout").write_bytes(scenes.read_file(reuse["stdout"], reuse_root))
        (directory / "compile.stderr").write_bytes(scenes.read_file(reuse["stderr"], reuse_root))
        reused = {"report": str(reuse_root / "report.json"), "report_sha256": digest(reuse_root / "report.json"),
                  "old_binary": str(old_binary), "compiled_binary_sha256": reuse["binary"]["sha256"],
                  "complete_instrumented_source_files": len(prepared), "source_closure_equal": True,
                  "note": "Compile command and outputs are the original compile; this run re-prepared and compared its complete closure."}
    scenes.require(binary.is_file(), "X7_WITHDRAWAL_PROBE_EXISTS")
    manifest_path = directory / "source-manifest.json"
    write_json(manifest_path, source_manifest(directory))
    return binary, {"binary": artifact(binary, out), "seconds": time.monotonic() - started,
                    "reused": reused,
                    "compile": artifact(directory / "compile.json", out),
                    "stdout": artifact(directory / "compile.stdout", out),
                    "stderr": artifact(directory / "compile.stderr", out),
                    "sources": artifact(manifest_path, out)}


def run(args):
    benchmark.validate_bundle(args.fixtures)
    out = scenes.new_output_directory(args.out, "X7_WITHDRAWAL_NEW_OUTPUT")
    module = importlib.import_module("tests.test_x7_performance")
    watched = [ROOT / TARGET, ROOT / "geometry-core/references.inc",
               ROOT / "tests/test_x7_performance.py", ROOT / "tests/diagnostics/x7_probe.inc",
               ROOT / "tests/diagnostics/x7_scenarios.py", Path(__file__).resolve()]
    source_hashes = {str(path.relative_to(ROOT)): digest(path) for path in watched}
    report = {"schema": "x7-withdrawals/1", "acceptance": False,
              "workflow_receipt": False, "argv": sys.argv, "cwd": str(ROOT),
              "fixture_bundle": str(args.fixtures.resolve()), "fixture_bundle_sha256": digest(args.fixtures),
              "source_sha256": source_hashes, "controls": [], "complete": False}
    write_json(out / "report.json", report)
    controls = [control for control in WITHDRAWALS if not args.only or control.name in args.only]
    previous = None
    previous_controls = {}
    previous_sha = None
    if args.reuse_builds:
        args.reuse_builds = args.reuse_builds.resolve()
        previous_path = args.reuse_builds / "report.json"
        previous_sha = digest(previous_path)
        previous = json.loads(previous_path.read_bytes())
        scenes.require(previous.get("schema") == "x7-withdrawals/1", "X7_REUSE_REPORT_SCHEMA")
        previous_controls = {row["name"]: row for row in previous["controls"]}
        scenes.require(len(previous_controls) == len(previous["controls"]), "X7_REUSE_UNIQUE_CONTROLS")
        report["reuse_report"] = {"path": str(previous_path), "sha256": previous_sha}
    try:
        print("X7_WITHDRAWAL_BUILD baseline", flush=True)
        baseline, baseline_build = build(module, out / "builds/baseline", out,
                                         reuse=previous["baseline_build"] if previous else None,
                                         reuse_root=args.reuse_builds)
        report["baseline_build"] = baseline_build
        write_json(out / "report.json", report)
        for control in controls:
            row = {"name": control.name, "method": control.method,
                   "expected_marker": control.marker, "mutation": {}, "state": "running"}
            report["controls"].append(row)
            print("X7_WITHDRAWAL_BUILD", control.name, flush=True)
            old = previous_controls.get(control.name)
            mutant, row["mutant_build"] = build(module, out / "builds" / control.name, out,
                                                 make_mutation(control, out, row["mutation"]),
                                                 reuse=old.get("mutant_build") if old else None,
                                                 reuse_root=args.reuse_builds)
            if old and old.get("mutant_build"):
                old_patch = scenes.read_file(old["mutation"]["patch"], args.reuse_builds)
                new_patch = scenes.read_file(row["mutation"]["patch"], out)
                scenes.require(old_patch == new_patch
                               and old["mutation"]["before_sha256"] == row["mutation"]["before_sha256"]
                               and old["mutation"]["after_sha256"] == row["mutation"]["after_sha256"],
                               "X7_REUSE_IDENTICAL_NAMED_PRODUCT_WITHDRAWAL", control.name)
                row["mutant_build"]["reused"]["named_patch_equal"] = True
            baseline_sha = baseline_build["binary"]["sha256"]
            mutant_sha = row["mutant_build"]["binary"]["sha256"]
            row["before"] = run_phase(args, out, control.name, "before", baseline, baseline_sha, control.method)
            row["withdraw"] = run_phase(args, out, control.name, "withdraw", mutant, mutant_sha, control.method)
            row["restore"] = run_phase(args, out, control.name, "restore", baseline, baseline_sha, control.method)
            row["exit_codes"] = [row[leg]["exit_code"] for leg in ("before", "withdraw", "restore")]
            killed = is_green(row["before"]) and is_named_red(row["withdraw"], control) and is_green(row["restore"])
            row["state"] = "killed" if killed else "survived" if is_green(row["withdraw"]) else "blocked"
            write_json(out / "report.json", report)
            print("X7_WITHDRAWAL", control.name, "/".join(map(str, row["exit_codes"])),
                  row["state"], "expected=" + control.marker, flush=True)
            if not killed:
                report["stop_reason"] = "Named assertion was not established; no error or timeout counts as a kill."
                write_json(out / "report.json", report)
                return 1 if row["state"] == "survived" else 2
        scenes.require(source_hashes == {str(path.relative_to(ROOT)): digest(path) for path in watched},
                       "X7_WITHDRAWAL_ORIGINAL_SOURCES_UNCHANGED")
        if previous is not None:
            scenes.require(digest(args.reuse_builds / "report.json") == previous_sha,
                           "X7_REUSE_REPORT_UNCHANGED")
        report["complete"] = True
        report["all_named_010"] = all(row["state"] == "killed" for row in report["controls"])
        write_json(out / "report.json", report)
        return 0
    except BaseException as error:
        report["exception"] = {"type": type(error).__name__, "message": str(error)}
        (out / "exception.txt").write_text(traceback.format_exc(), encoding="utf-8")
        write_json(out / "report.json", report)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--only", action="append", choices=[control.name for control in WITHDRAWALS])
    parser.add_argument("--reuse-builds", type=Path,
                        help="Re-prepare and exactly compare every C/header/include plus named patch before reusing a pinned prior compile.")
    parser.add_argument("--phase-timeout", type=int, default=120)
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--binary", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--binary-sha256", help=argparse.SUPPRESS)
    parser.add_argument("--fixtures-sha256", help=argparse.SUPPRESS)
    parser.add_argument("--artifacts", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--child-result", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--method", choices=[SUCCESS, FAILURE], help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        if not all((args.binary, args.binary_sha256, args.fixtures_sha256,
                    args.artifacts, args.child_result, args.method)):
            parser.error("child arguments are incomplete")
        return child(args)
    if args.out is None or not (1 <= args.phase_timeout <= 300):
        parser.error("--out and a phase timeout from 1 through 300 seconds are required")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
