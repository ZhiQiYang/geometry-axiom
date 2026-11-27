#!/usr/bin/env python3
"""Replay the R14 candidate-query product withdrawals in isolated source copies.

Run after applying P and T, for example::

    python -B tests/diagnostics/r14_candidate_query_mutations.py \
        --out /tmp/r14-candidate-mutations --jobs 2

``--case NAME`` is repeatable. Each mutation changes an actual C include, builds
through the unmodified tests/binaries.py (including its original compiler flags,
timeouts, smoke test, and fingerprint writer), and launches three separate
unittest processes. A kill requires 0/1/0, exactly one named test per process,
only the specified assertion failure(s), no errors/skips/expected failures, and
fresh binaries. Compile failures and missing P are blocked, never killed.

The immutable baseline binary is shared. After restoring every copied source
byte, binaries.py revalidates/reuses that original binary; the restored test is
a new process. Each mutant has its own source tree and OUT_DIR. Raw subprocess
stdout/stderr, machine reports, source hashes and patches are retained under
--out. Every subprocess has its own TMPDIR under --out; this changes storage,
not compiler flags or test bounds. Timed-out phases are blocked, never kills.
After a blocked case, remaining batches are marked not-run. This diagnostic does not register official
mutation evidence, modify the working product tree, or write a fingerprint
sidecar itself.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
import unittest


# The seal judge can include a native build. Bound the whole phase by the
# suite budget; the compiler (900 s) and smoke (30 s) keep their own limits.
JUDGE_TIMEOUT = 1200
BUILD_TIMEOUT = 1200
SOURCE = "geometry-web/grid_subdivision_bridge.inc"
TEST_MODULE = "tests.test_r14_candidate_query.R14CandidateQuery."
TEST_01 = "test_01_create_rule_reads_after_before_missing_and_commits_same_candidate"
TEST_02 = "test_02_source_edit_distinguishes_both_sides_from_live_and_preserves_history"
TEST_07 = "test_07_token_kind_mismatch_unknown_owner_and_invalid_queries_do_not_consume"
TEST_13 = "test_13_real_foreign_candidate_owners_are_rejected_without_consuming_their_tokens"
TEST_14 = "test_14_open_history_group_refuses_read_then_same_token_recovers"
TEST_15 = "test_15_current_seal_guard_is_independent_of_revision_and_does_not_consume"
RUNNER = "tests/diagnostics/r14_candidate_query_mutations.py"
TEST_FILES = (
    "tests/__init__.py", "tests/binaries.py", "tests/_bridge.py",
    "tests/test_r14_candidate_query.py", "tests/test_assembly_rules.py",
    "tests/test_section_profile_native.py", "tests/test_panel_fill_finish_surface.py",
    "tests/diagnostics/r14_panel_next_oracle.py",
    "tests/diagnostics/r14_candidate_query_seal.c", RUNNER,
)


def mutation(name, test, tag, before, after):
    return dict(name=name, test=TEST_MODULE + test, tag="R14CQ_" + tag,
                source=SOURCE, before=before, after=after)


CASES = [
    mutation("AFTER_USES_LIVE", TEST_01, "CANDIDATE_AVAILABLE",
             "&g_preview.transaction->before:&g_preview.transaction->after;",
             "&g_preview.transaction->before:&g_world;"),
    mutation("BEFORE_USES_AFTER", TEST_02, "SOURCE_BEFORE_MAIN_ALONG",
             "&g_preview.transaction->before:&g_preview.transaction->after;",
             "&g_preview.transaction->after:&g_preview.transaction->after;"),
    mutation("SOURCE_USES_LIVE_WORLD", TEST_02, "SOURCE_AFTER_MAIN_ALONG",
             "json_grid_system(world,source);", "json_grid_system(&g_world,source);"),
    mutation("DROP_OWNER_GATE", TEST_13, "REJECT",
             "if (!mine) {", "if (false && !mine) {"),
    mutation("DROP_TOKEN_IDENTITY", TEST_07, "REJECT",
             "|| !g_preview.transaction || g_preview.token!=token)",
             "|| !g_preview.transaction)"),
    mutation("DROP_GROUPING_GUARD", TEST_14, "REJECT",
             "if (g_history.grouping || g_preview.revision!=g_definition_revision ||",
             "if (g_preview.revision!=g_definition_revision ||"),
    mutation("METRICS_OMIT_GAP", TEST_01, "METRICS",
             "Coord pitch=geo_grid_axis_pitch(&source->axis[axis]);",
             "Coord pitch=geo_grid_axis_pitch(&source->axis[axis])-source->axis[axis].gap;"),
    mutation("SKEW_SEGMENT_ENDPOINT", TEST_01, "NEW_RULE_COORDINATES_FULL_2D_SEGMENT",
             "(long long)segment->end.u,", "(long long)(segment->end.u+1),"),
    mutation("NO_CURRENT_SEAL", TEST_15, "SEAL_STALE",
             "!app_world_candidate_current(g_preview.transaction,&g_world)) {",
             "false) {"),
]
BY_NAME = {case["name"]: case for case in CASES}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def load_binaries(root):
    spec = importlib.util.spec_from_file_location("binaries", root / "tests/binaries.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_mutation(data, case):
    before = case["before"].encode()
    after = case["after"].encode()
    if before not in data:
        before = before.replace(b"\n", b"\r\n")
        after = after.replace(b"\n", b"\r\n")
    if data.count(before) != 1:
        raise ValueError("P_MISSING_OR_CHANGED: %s anchor count is %d" %
                         (case["name"], data.count(before)))
    changed = data.replace(before, after, 1)
    if changed == data:
        raise ValueError("mutation does not change source bytes")
    return changed


def snapshot(root, target, cases):
    implementation = (root / SOURCE).read_bytes()
    dispatch = (root / "geometry-web/web_bridge.c").read_bytes()
    if (b"static void cmd_grid_rule_candidate_query(" not in implementation or
            b'"grid-rule-candidate-query"' not in dispatch):
        raise ValueError("P_MISSING_OR_CHANGED: candidate-query product P is required")
    for case in cases:
        source_mutation(implementation, case)
    binaries = load_binaries(root)
    paths = {p.relative_to(root) for p in binaries._scan_shared() if p.is_file()}
    paths.update(Path(p) for p in TEST_FILES)
    # Include vendor C headers too if present: the native fingerprint intentionally
    # excludes vendor, while the compiler can still include those files.
    for top in ("geometry-core", "geometry-web", "geometry-app", "geometry-templates"):
        for vendor in (root / top).rglob("vendor"):
            if vendor.is_dir():
                paths.update(p.relative_to(root) for p in vendor.rglob("*") if p.is_file())
    for optional in ("tests/diagnostics/__init__.py",):
        if (root / optional).is_file():
            paths.add(Path(optional))
    records = {}
    for relative in sorted(paths):
        data = (root / relative).read_bytes()
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        records[relative.as_posix()] = sha(data)
    return records


def copied_bytes_equal(root, records):
    return all((root / path).is_file() and sha((root / path).read_bytes()) == digest
               for path, digest in records.items())


def build_child(root, out, report_path):
    binaries = load_binaries(root)
    binaries.OUT_DIR = out
    code = binaries.main(["build", "bridge"])
    info = binaries.inspect_one(binaries.BY_NAME["bridge"])
    report = dict(exit_code=code, fresh=info.state == "fresh", info=info.as_dict(),
                  fingerprint=info.fingerprint)
    if info.state == "fresh":
        report.update(binary_sha256=sha(info.path.read_bytes()),
                      sidecar_sha256=sha(info.path.with_name(info.path.name +
                                                           binaries.SIDECAR_SUFFIX).read_bytes()))
    write_json(report_path, report)
    return code if code else (0 if report["fresh"] else 2)


class StructuredResult(unittest.TextTestResult):
    """Keep exception messages, not traceback source lines, for assertion tags."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assertions = []
        self.exceptions = []

    @staticmethod
    def record(test, err):
        return {"test": test.id(), "type": err[0].__name__, "message": str(err[1])}

    def addFailure(self, test, err):
        self.assertions.append(self.record(test, err))
        super().addFailure(test, err)

    def addError(self, test, err):
        self.exceptions.append(self.record(test, err))
        super().addError(test, err)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            records = self.assertions if issubclass(err[0], test.failureException) else self.exceptions
            records.append(self.record(subtest, err))
        super().addSubTest(test, subtest, err)


def judge_child(root, executable, test, report_path):
    sys.path.insert(0, str(root))
    os.environ["GEOMETRY_TEST_BRIDGE"] = str(executable)
    os.environ["GEOMETRY_ENGINEERING_BRIDGE"] = str(executable)
    suite = unittest.defaultTestLoader.loadTestsFromName(test)
    result = unittest.TextTestRunner(verbosity=2, resultclass=StructuredResult).run(suite)
    forbidden = bool(result.errors or result.skipped or result.expectedFailures or
                     result.unexpectedSuccesses or result.testsRun != 1)
    code = 2 if forbidden else (0 if result.wasSuccessful() else 1)
    report = dict(test=test, tests_run=result.testsRun, successful=result.wasSuccessful(),
                  failures=result.assertions, errors=result.exceptions,
                  skipped=[(str(t), reason) for t, reason in result.skipped],
                  expected_failures=len(result.expectedFailures),
                  unexpected_successes=len(result.unexpectedSuccesses), exit_code=code)
    write_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return code


def process(root, label, directory, arguments):
    report_path = directory / (label + ".json")
    command = [sys.executable, "-B", str(root / RUNNER), *arguments, str(report_path)]
    temporary = directory / (label + ".tmp")
    temporary.mkdir()
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(temporary))
    is_judge = arguments[0] == "--_judge"
    timeout = JUDGE_TIMEOUT if is_judge else BUILD_TIMEOUT
    timeout_error = None
    start = time.monotonic()
    with (directory / (label + ".stdout.log")).open("wb") as stdout, \
            (directory / (label + ".stderr.log")).open("wb") as stderr:
        child = subprocess.Popen(command, cwd=root, env=environment, stdout=stdout, stderr=stderr,
                                 start_new_session=os.name != "nt")
        try:
            child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            tag = "R14CQ_JUDGE_TIMEOUT" if is_judge else "R14CQ_BUILD_TIMEOUT"
            timeout_error = f"{tag}: {label} exceeded {timeout}s"
            # The judge may itself be stuck reading a live bridge. Kill the
            # phase tree, not just the Python parent, before restoring bytes.
            try:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/T", "/F", "/PID", str(child.pid)],
                                   stdout=stdout, stderr=stderr, timeout=10, check=True)
                else:
                    os.killpg(child.pid, signal.SIGKILL)
            except (OSError, subprocess.SubprocessError) as exc:
                timeout_error += f"; tree cleanup: {exc}"
                child.kill()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                timeout_error += "; child did not exit after kill"
            stderr.write(("\n" + timeout_error + "\n").encode("utf-8"))
    result = dict(command=command, exit_code=child.returncode,
                  seconds=round(time.monotonic() - start, 3), tmpdir=str(temporary),
                  report=read_json(report_path))
    if timeout_error:
        result["timeout_error"] = timeout_error
    write_json(directory / (label + ".process.json"), result)
    if timeout_error:
        raise TimeoutError(timeout_error)
    return result


def build(root, out, directory, label):
    return process(root, label, directory, ["--_build", str(root), str(out)])


def judge(root, executable, case, directory, label):
    result = process(root, label, directory,
                     ["--_judge", str(root), str(executable), case["test"]])
    # A reply timeout inside the judge is an infrastructure error even during
    # the mutant phase, not a wrong assertion or a surviving mutant.
    if isinstance(result["report"], dict):
        for error in result["report"].get("errors", []):
            if error["type"] == "TimeoutError":
                raise TimeoutError(f"{label}: {error['message']}")
    return result


def fresh(result):
    report = result.get("report")
    return (result["exit_code"] == 0 and isinstance(report, dict) and
            report.get("exit_code") == 0 and report.get("fresh") is True)


def judged(result, expected, tag):
    report = result.get("report")
    if not (result["exit_code"] == expected and isinstance(report, dict) and
            report.get("exit_code") == expected and report.get("tests_run") == 1 and
            not report.get("errors") and not report.get("skipped") and
            not report.get("expected_failures") and not report.get("unexpected_successes")):
        return False
    failures = report.get("failures", [])
    if expected == 0:
        return report.get("successful") is True and not failures
    return (report.get("successful") is False and bool(failures) and
            all(tag in failure["message"] and failure["type"] == "AssertionError"
                for failure in failures))


def run_case(case, source, records, baseline_build, baseline_out, output, baseline_lock):
    directory = output / case["name"]
    directory.mkdir()
    root = directory / "source"
    shutil.copytree(source, root)
    report = dict(name=case["name"], test=case["test"], assertion_tag=case["tag"],
                  status="blocked", passed=False, baseline_build=baseline_build)
    path = root / case["source"]
    original = path.read_bytes()
    try:
        baseline_exe = Path(baseline_build["report"]["info"]["path"])
        report["baseline"] = judge(root, baseline_exe, case, directory, "baseline-test")
        if not judged(report["baseline"], 0, case["tag"]):
            raise ValueError("baseline is not one successful unskipped test")
        changed = source_mutation(original, case)
        path.write_bytes(changed)
        report["mutation"] = dict(source=case["source"], before_sha256=sha(original),
                                  after_sha256=sha(changed))
        patch = "".join(difflib.unified_diff(original.decode().splitlines(True),
                                            changed.decode().splitlines(True),
                                            "a/" + case["source"], "b/" + case["source"]))
        (directory / "withdrawal.patch").write_text(patch, encoding="utf-8")
        report["mutant_build"] = build(root, directory / "mutant-bin", directory, "mutant-build")
        if not fresh(report["mutant_build"]):
            raise ValueError("mutant build did not produce a fresh bridge")
        mutant_exe = Path(report["mutant_build"]["report"]["info"]["path"])
        report["mutant"] = judge(root, mutant_exe, case, directory, "mutant-test")
    except Exception as exc:
        report["reason"] = "%s: %s" % (type(exc).__name__, exc)
    finally:
        path.write_bytes(original)
    try:
        report["all_copied_bytes_restored"] = copied_bytes_equal(root, records)
        if not report["all_copied_bytes_restored"]:
            raise ValueError("restored source/test closure differs from baseline")
        with baseline_lock:
            report["restored_build"] = build(root, baseline_out, directory, "restored-build")
        if not fresh(report["restored_build"]):
            raise ValueError("restored source did not verify a fresh baseline bridge")
        if report["restored_build"]["report"]["binary_sha256"] != baseline_build["report"]["binary_sha256"]:
            raise ValueError("shared baseline binary bytes changed")
        report["restored"] = judge(root, baseline_exe, case, directory, "restored-test")
        valid = ("reason" not in report and judged(report["baseline"], 0, case["tag"]) and
                 judged(report["mutant"], 1, case["tag"]) and
                 judged(report["restored"], 0, case["tag"]))
        report.update(passed=valid, status="killed" if valid else
                      ("blocked" if "reason" in report else "not-killed"))
        if "mutant" in report:
            report["exit_codes"] = [report[key]["exit_code"] for key in ("baseline", "mutant", "restored")]
    except Exception as exc:
        report["reason"] = "%s: %s" % (type(exc).__name__, exc)
    write_json(directory / "report.json", report)
    print(json.dumps({key: report[key] for key in ("name", "status", "passed", "exit_codes", "reason")
                      if key in report}, ensure_ascii=False), flush=True)
    return report


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--_build" and len(argv) == 4:
        return build_child(Path(argv[1]), Path(argv[2]), Path(argv[3]))
    if argv and argv[0] == "--_judge" and len(argv) == 5:
        return judge_child(Path(argv[1]), Path(argv[2]), argv[3], Path(argv[4]))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, help="new artifact directory outside the repository")
    parser.add_argument("--baseline-cache", type=Path,
                        help="optional isolated OUT_DIR; original binaries.py still verifies/builds it")
    parser.add_argument("--case", action="append", choices=list(BY_NAME))
    parser.add_argument("--jobs", type=int, choices=(1, 2), default=1)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)
    if args.list:
        print(json.dumps(CASES, ensure_ascii=False, indent=2))
        return 0
    if args.out is None:
        parser.error("--out is required (raw artifacts are never silently discarded)")
    root, output = args.repo.resolve(), args.out.resolve()
    if output == root or root in output.parents:
        parser.error("--out must be outside the source repository")
    output.mkdir(parents=True, exist_ok=False)
    report = dict(kind="product-source-mutations-not-official-ledger", passed=False,
                  repository=str(root), runner_sha256=sha(Path(__file__).read_bytes()), cases=[])
    selected = [BY_NAME[name] for name in dict.fromkeys(args.case or BY_NAME)]
    try:
        source = output / "baseline-source"
        baseline_out = args.baseline_cache.resolve() if args.baseline_cache else output / "baseline-bin"
        if baseline_out == root or root in baseline_out.parents:
            raise ValueError("baseline OUT_DIR must be outside the repository")
        records = snapshot(root, source, selected)
        write_json(output / "closure.json", records)
        report["closure_sha256"] = sha((output / "closure.json").read_bytes())
        baseline_build = build(source, baseline_out, output, "baseline-build")
        report["baseline_build"] = baseline_build
        if not fresh(baseline_build):
            raise ValueError("baseline build failed or is not fresh; no product kill is recorded")
        lock = threading.Lock()
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
            for first in range(0, len(selected), args.jobs):
                batch = selected[first:first + args.jobs]
                futures = [executor.submit(run_case, case, source, records, baseline_build,
                                           baseline_out, output, lock) for case in batch]
                results = [future.result() for future in futures]
                report["cases"].extend(results)
                if any(case["status"] == "blocked" for case in results):
                    report["cases"].extend(dict(name=case["name"], passed=False, status="not-run",
                                                reason="stopped after blocked case")
                                           for case in selected[first + args.jobs:])
                    break
        report["baseline_closure_unchanged"] = copied_bytes_equal(source, records)
        report["passed"] = (report["baseline_closure_unchanged"] and
                            all(case["passed"] for case in report["cases"]))
    except Exception as exc:
        report.update(status="blocked", reason="%s: %s" % (type(exc).__name__, exc))
    write_json(output / "report.json", report)
    print(json.dumps(dict(passed=report["passed"], report=str(output / "report.json"),
                          reason=report.get("reason")), ensure_ascii=False), flush=True)
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
