#!/usr/bin/env python3
"""Manual R03 R-butt source-withdrawal diagnostics; never a formal receipt.

No arguments lists six named withdrawals. Explicitly run one or all:

  python -B tests/diagnostics/r03_rbutt_withdrawals.py --only W_APPLY_SHIFT --out /external/diagnostics
  python -B tests/diagnostics/r03_rbutt_withdrawals.py --all --out /external/diagnostics

The live checkout is read-only. A complete private source copy is used, with
only caches/Git/build artifacts excluded. Its original tests/binaries.py is
imported unchanged; only OUT_DIR is assigned to a private output directory.
Every phase invokes its real build/freshness checks and its real selected
test_framing_template_rbutt.py method. Source bytes are restored in finally.

A qualified withdrawal requires actual baseline/test/restored exits 0/1/0.
The middle result must contain only AssertionError failures of the selected
test, each carrying its named assertion marker. The selected method uses
unittest failfast, avoiding a pending-preview cascade after its first failure;
successful baseline/restored methods still execute all their subtests.
Compilation failures, errors,
crashes, timeouts, missing imports, skipped tests and unrelated assertions do
not count. Each build has a <=360 s deadline and each test <=60 s; timeout or
interruption terminates the process group, including compiler/bridge children.

Raw stdout/stderr, complete argv, return codes and an explicitly nonofficial
JSON report stay under --out. GEOMETRY_*RECEIPT* variables are removed, so this
diagnostic cannot overwrite the formal suite's derived receipt directory.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import traceback
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[2]
W = "geometry-templates/woodworking/native/flat_ceiling_rbutt.h"
H = "geometry-web/framing_template_bridge.inc"
TEST_FILE = "tests/test_framing_template_rbutt.py"
TEST_MODULE = "test_framing_template_rbutt"
TEST_CLASS = "FramingTemplateRbutt"
TEST_PREFIX = "R03R_WITHDRAWAL_TEST_RESULT "
BUILD_PREFIX = "R03R_WITHDRAWAL_BUILD_RESULT "
SCHEMA = "r03r-withdrawal-diagnostic/1"

# Exact byte anchors are local proof obligations. An absent/repeated anchor is
# an infrastructure failure, never a surviving or killed product mutation.
WITHDRAWALS = {
    "W_APPLY_SHIFT": {
        "source": W,
        "edits": [("shifts[i]=shift; /* R03R_APPLY_SHIFT */",
                   "shifts[i]=0; /* R03R_APPLY_SHIFT */")],
        "test": "test_R02_four_corners_both_axes_every_member_and_panel",
        "marker": "R03R_EVERY_MEMBER",
        "meaning": "Discard the computed main-member shift.",
    },
    "W_EXACT_THRESHOLD": {
        "source": W,
        "edits": [
            ("wood_flat_width_enough(hh-gu-left,xnum,xden);",
             "wood_flat_width_enough(hh-gu-left,xnum+xden,xden);"),
            ("wood_flat_width_enough(lh-gl-right,xnum,xden); /* R03R_EXACT_THRESHOLD */",
             "wood_flat_width_enough(lh-gl-right,xnum+xden,xden); /* R03R_EXACT_THRESHOLD */"),
        ],
        "test": "test_R04_exact_rational_threshold_and_full_r43",
        "marker": "R03R_EXACT_THRESHOLD",
        "meaning": "Incorrectly require X+1 mm, rejecting the exact-X boundary.",
    },
    "W_TIE_DIRECTION": {
        "source": W,
        "edits": [("if(positive&&(!negative||right<left))shift=right; /* R03R_NEAREST_TIE_NEGATIVE */",
                   "if(positive&&(!negative||right<=left))shift=right; /* R03R_NEAREST_TIE_NEGATIVE */")],
        "test": "test_R05_existing_contact_and_nearest_tie_negative",
        "marker": "R03R_NEAREST_TIE_NEGATIVE",
        "meaning": "Choose the positive side instead of the negative side in a true tie.",
    },
    "W_SECONDARY_ENDPOINTS": {
        "source": W,
        "edits": [("int64_t left=edges[i][1],right=edges[i+1][0]; /* R03R_REBUILD_SECONDARY */",
                   "int64_t left=edges[i][1]-(i?shifts[i-1]:0),right=edges[i+1][0]-(i+1<n-1?shifts[i]:0); /* R03R_REBUILD_SECONDARY */")],
        "test": "test_R02_four_corners_both_axes_every_member_and_panel",
        "marker": "R03R_EVERY_MEMBER",
        "meaning": "Use the old unshifted secondary endpoints beside a shifted main.",
    },
    "H_ORIGINAL_SEAM_KEY": {
        "source": H,
        "edits": [("(long long)framing_template_k(c,main_cross,c->plan.seams[main_cross][k]),name); /* R03R_LIVE_ORIGINAL_SEAM */",
                   "(long long)(framing_template_k(c,main_cross,c->plan.seams[main_cross][k])+1),name); /* R03R_LIVE_ORIGINAL_SEAM */")],
        "test": "test_R03_translated_and_odd_gap_source_floor",
        "marker": "R03R_ODD_GAP_SOURCE_FLOOR",
        "meaning": "Attach the live offset guide to the next signed seam key.",
    },
    "H_COMPLETE_R43_GATE": {
        "source": H,
        "edits": [("for(size_t i=0;i<support.part_count&&ok;++i)if(!support.parts[i].supported){",
                   "for(size_t i=0;i<support.part_count&&ok;++i)if(false&&!support.parts[i].supported){")],
        "test": "test_R06_ft02_and_native_gap_remain_real_rejections",
        "marker": "R03R_COMPLETE_R43_REQUIRED",
        "meaning": "Remove final per-segment R43 refusal while keeping the native transaction path.",
    },
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def within(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def test_id(spec):
    return TEST_MODULE + "." + TEST_CLASS + "." + spec["test"]


def replace_exact(original, spec):
    changed = original
    for before, after in spec["edits"]:
        old, new = before.encode("utf-8"), after.encode("utf-8")
        if original.count(old) != 1 or changed.count(old) != 1:
            raise RuntimeError("R03R_WITHDRAWAL_EXACT_ANCHOR: " + spec["source"] + ": " + before)
        changed = changed.replace(old, new, 1)
    if changed == original:
        raise RuntimeError("R03R_WITHDRAWAL_NO_SOURCE_CHANGE")
    return changed


def copied_ignores(directory, names):
    skipped = {".git", "__pycache__", "node_modules", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv"}
    result = []
    for name in names:
        path = Path(directory) / name
        if name in skipped or name.endswith((".pyc", ".pyo", ".o", ".obj", ".exe", ".fingerprint.json")):
            result.append(name)
        elif path.is_symlink() and path.is_dir():
            # Do not accidentally follow an external directory or a cycle.
            raise RuntimeError("R03R_WITHDRAWAL_DIRECTORY_SYMLINK: " + str(path))
    return result


def _kill_group(process):
    """Terminate every child in the independently created process group."""
    actions = []
    if os.name == "nt":
        try:
            killer = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    timeout=5, check=False,
                                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            actions.append({"taskkill_exit": killer.returncode})
        except (OSError, subprocess.TimeoutExpired) as error:
            actions.append({"taskkill_error": type(error).__name__})
        if process.poll() is None:
            process.kill()
    else:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(process.pid, sig)
                actions.append({"signal": sig.name})
            except ProcessLookupError:
                break
            if sig == signal.SIGTERM:
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
                # Kill the whole group even if only the parent already exited.
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        actions.append({"reap_timeout": True})
    return actions


def run_bounded(argv, *, cwd, env, limit, log_prefix):
    stdout_path = Path(str(log_prefix) + ".stdout.log")
    stderr_path = Path(str(log_prefix) + ".stderr.log")
    started = time.monotonic()
    row = {"argv": argv, "cwd": str(cwd), "timeout_seconds": limit,
           "stdout_log": str(stdout_path), "stderr_log": str(stderr_path),
           "timed_out": False, "returncode": None}
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, **options)
        except OSError as error:
            row["launch_error"] = type(error).__name__ + ": " + str(error)
        else:
            try:
                row["returncode"] = process.wait(timeout=limit)
            except subprocess.TimeoutExpired:
                row["timed_out"] = True
                row["termination"] = _kill_group(process)
                row["returncode"] = process.returncode
            except BaseException:
                _kill_group(process)
                raise
    row["seconds"] = round(time.monotonic() - started, 3)
    row["stdout_sha256"] = sha(stdout_path.read_bytes())
    row["stderr_sha256"] = sha(stderr_path.read_bytes())
    return row


class RecordedResult(unittest.TextTestResult):
    """Record real unittest outcomes, including the owner of failed subtests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faults = []

    def _record(self, test, error, category, subtest=None):
        kind, value, _ = error
        self.faults.append({"owner_test_id": test.id(),
                            "subtest_id": subtest.id() if subtest is not None else None,
                            "category": category, "exception_type": kind.__name__,
                            "is_assertion_error": issubclass(kind, AssertionError),
                            "message": str(value)})

    def addFailure(self, test, error):
        self._record(test, error, "failure")
        super().addFailure(test, error)

    def addError(self, test, error):
        self._record(test, error, "error")
        super().addError(test, error)

    def addSubTest(self, test, subtest, error):
        if error is not None:
            self._record(test, error, "failure" if issubclass(error[0], test.failureException) else "error", subtest)
        super().addSubTest(test, subtest, error)


def worker(action, identifier, binary_dir):
    """Executed from the copied script: every imported ROOT is the private one."""
    try:
        sys.path.insert(0, str(ROOT / "tests"))
        binaries = importlib.import_module("binaries")
        if binaries.ROOT.resolve() != ROOT or Path(binaries.__file__).resolve() != ROOT / "tests/binaries.py":
            raise RuntimeError("R03R_WITHDRAWAL_WRONG_FRESHNESS_ROOT")
        binaries.OUT_DIR = Path(binary_dir).resolve()  # The only registry setting changed.
        if within(binaries.OUT_DIR, ROOT):
            raise RuntimeError("R03R_WITHDRAWAL_BINARY_DIR_MUST_BE_EXTERNAL")
        if action == "build":
            code = binaries.main(["build", "bridge"])
            if code == 0:
                binaries.require_fresh("bridge", binaries.BY_NAME["bridge"].path)
            info = binaries.inspect_one(binaries.BY_NAME["bridge"])
            print(BUILD_PREFIX + json.dumps({"exit": code, "freshness": info.as_dict(),
                                            "source_fingerprint": info.fingerprint,
                                            "registry_root": str(binaries.ROOT)}, ensure_ascii=False), flush=True)
            return code
        path = binaries.require_fresh("bridge", binaries.BY_NAME["bridge"].path)
        os.environ["GEOMETRY_TEST_BRIDGE"] = path
        os.environ["GEOMETRY_ENGINEERING_BRIDGE"] = path
        module = importlib.import_module(TEST_MODULE)
        if Path(module.__file__).resolve() != ROOT / TEST_FILE or module.ROOT.resolve() != ROOT:
            raise RuntimeError("R03R_WITHDRAWAL_WRONG_TEST_ROOT")
        identifier_full = test_id(WITHDRAWALS[identifier])
        selected = unittest.defaultTestLoader.loadTestsFromName(identifier_full)
        if selected.countTestCases() != 1:
            raise RuntimeError("R03R_WITHDRAWAL_EXPECTED_EXACTLY_ONE_REAL_TEST")
        result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult, failfast=True).run(selected)
        payload = {"test_id": identifier_full, "tests_run": result.testsRun,
                   "successful": result.wasSuccessful(), "faults": result.faults,
                   "errors": len(result.errors), "failures": len(result.failures),
                   "skipped": len(result.skipped), "expected_failures": len(result.expectedFailures),
                   "unexpected_successes": len(result.unexpectedSuccesses),
                   "source_root": str(ROOT), "binary": path, "failfast": True}
        print(TEST_PREFIX + json.dumps(payload, ensure_ascii=False), flush=True)
        if result.testsRun != 1 or result.errors or result.skipped or result.expectedFailures or result.unexpectedSuccesses:
            return 2
        return 0 if result.wasSuccessful() else 1
    except Exception as error:
        traceback.print_exc()
        print("R03R_WITHDRAWAL_INFRASTRUCTURE_ERROR " + json.dumps({"type": type(error).__name__, "message": str(error)}), flush=True)
        return 2


def result_payload(row, prefix):
    lines = Path(row["stdout_log"]).read_text(encoding="utf-8", errors="replace").splitlines()
    matched = [line[len(prefix):] for line in lines if line.startswith(prefix)]
    if len(matched) != 1:
        return None
    try:
        value = json.loads(matched[0])
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def classify_test(row, spec, wanted_exit):
    """Never infer a kill from stderr text, a nonzero exit alone, or a timeout."""
    payload = result_payload(row, TEST_PREFIX)
    row["unittest"] = payload
    if row["timed_out"] or row.get("launch_error") or row["returncode"] != wanted_exit or payload is None:
        return False
    if payload.get("test_id") != test_id(spec) or payload.get("tests_run") != 1:
        return False
    if any(payload.get(key) != 0 for key in ("errors", "skipped", "expected_failures", "unexpected_successes")):
        return False
    faults = payload.get("faults")
    if not isinstance(faults, list):
        return False
    if wanted_exit == 0:
        return payload.get("successful") is True and payload.get("failures") == 0 and not faults
    if wanted_exit != 1 or payload.get("successful") is not False or not faults or payload.get("failures") != len(faults):
        return False
    marker = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(spec["marker"]) + r"(?![A-Za-z0-9_])")
    return all(item.get("owner_test_id") == test_id(spec) and item.get("category") == "failure"
               and item.get("is_assertion_error") is True and marker.search(item.get("message", ""))
               for item in faults)


def run_phase(private, binary_dir, logs, identifier, phase, env, build_limit, test_limit):
    spec = WITHDRAWALS[identifier]
    script = private / "tests/diagnostics/r03_rbutt_withdrawals.py"
    common = [sys.executable, "-B", str(script), "--binary-dir", str(binary_dir), "--worker-case", identifier]
    row = {"phase": phase, "source_sha256": sha((private / spec["source"]).read_bytes())}
    row["build"] = run_bounded(common + ["--worker", "build"], cwd=private, env=env,
                               limit=build_limit, log_prefix=logs / (phase + ".build"))
    build_data = result_payload(row["build"], BUILD_PREFIX)
    row["build"]["registry_result"] = build_data
    if row["build"]["timed_out"] or row["build"].get("launch_error") or row["build"]["returncode"] != 0 or not build_data or build_data.get("freshness", {}).get("state") != "fresh":
        row["qualified"] = False
        row["reason"] = "BUILD_OR_FRESHNESS_FAILURE; selected native test was not run"
        return row
    row["test"] = run_bounded(common + ["--worker", "test"], cwd=private, env=env,
                              limit=test_limit, log_prefix=logs / (phase + ".test"))
    wanted = 1 if phase == "withdrawn" else 0
    row["qualified"] = bool(classify_test(row["test"], spec, wanted))
    row["reason"] = "EXPECTED_NAMED_ASSERTION" if row["qualified"] and wanted == 1 else "PASSED" if row["qualified"] else "UNQUALIFIED_TEST_OUTCOME"
    return row


def supervise(identifiers, source, out, build_limit, test_limit):
    source, out = source.resolve(), out.resolve()
    if within(out, source):
        raise ValueError("--out must be outside the source checkout")
    critical = {W, H, TEST_FILE, "tests/binaries.py", "tests/diagnostics/r03_retreat_oracle.py",
                "tests/diagnostics/r03_rbutt_withdrawals.py"}
    originals = {rel: (source / rel).read_bytes() for rel in critical}
    for identifier in identifiers:
        replace_exact(originals[WITHDRAWALS[identifier]["source"]], WITHDRAWALS[identifier])
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = out / ("r03r-withdrawals-" + stamp + "-" + uuid.uuid4().hex[:8])
    run_dir.mkdir(parents=True)
    private, binary_dir = run_dir / "source", run_dir / "binaries"
    report_path = run_dir / "diagnostic-report.json"
    report = {"schema": SCHEMA, "official_receipt": False, "formal_suite_member": False,
              "source_checkout": str(source), "private_source": str(private),
              "private_binary_dir": str(binary_dir), "build_flags_changed": False,
              "freshness_disabled": False, "source_checkout_written": False,
              "selected_test_failfast": True,
              "source_sha256": {rel: sha(data) for rel, data in sorted(originals.items())},
              "build_timeout_seconds": build_limit, "test_timeout_seconds": test_limit,
              "withdrawals": [], "ok": False}

    def save():
        # This file is diagnostic-only; no run_all receipt or evidence index.
        temporary = report_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(report_path)

    save()
    try:
        shutil.copytree(source, private, symlinks=False, ignore=copied_ignores)
        for rel, data in originals.items():
            if (private / rel).read_bytes() != data or (source / rel).read_bytes() != data:
                raise RuntimeError("R03R_WITHDRAWAL_SNAPSHOT_CHANGED: " + rel)
        (run_dir / "tmp").mkdir()
        env = {key: value for key, value in os.environ.items()
               if not (key.startswith("GEOMETRY_") and "RECEIPT" in key.upper())}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        for key in ("TMPDIR", "TMP", "TEMP"):
            env[key] = str(run_dir / "tmp")
        for identifier in identifiers:
            spec = WITHDRAWALS[identifier]
            original = originals[spec["source"]]
            target = private / spec["source"]
            logs = run_dir / identifier
            logs.mkdir()
            row = {"id": identifier, "source": spec["source"], "test_id": test_id(spec),
                   "assertion_marker": spec["marker"], "edits": spec["edits"],
                   "original_sha256": sha(original), "phases": []}
            report["withdrawals"].append(row)
            try:
                if target.read_bytes() != original:
                    raise RuntimeError("R03R_WITHDRAWAL_BASELINE_BYTES_CHANGED")
                baseline = run_phase(private, binary_dir, logs, identifier, "baseline", env, build_limit, test_limit)
                row["phases"].append(baseline)
                save()
                if baseline["qualified"]:
                    changed = replace_exact(original, spec)
                    target.write_bytes(changed)
                    row["withdrawn_sha256"] = sha(changed)
                    row["phases"].append(run_phase(private, binary_dir, logs, identifier, "withdrawn", env, build_limit, test_limit))
                else:
                    row["withdrawal_not_run"] = "Baseline did not pass; no kill can be claimed."
            finally:
                target.write_bytes(original)
                row["source_restored_exactly"] = target.read_bytes() == original
                save()
            # A real restored-source build/freshness check AND native test. No
            # baseline exit or cached test result is copied into this phase.
            row["phases"].append(run_phase(private, binary_dir, logs, identifier, "restored", env, build_limit, test_limit))
            row["test_exits"] = [phase.get("test", {}).get("returncode") for phase in row["phases"]]
            row["qualified"] = (len(row["phases"]) == 3 and row["test_exits"] == [0, 1, 0]
                                and row["source_restored_exactly"] and all(phase["qualified"] for phase in row["phases"]))
            save()
            print(identifier + " " + ("QUALIFIED 0/1/0" if row["qualified"] else "UNQUALIFIED") + " " + str(logs), flush=True)
        report["ok"] = all(row.get("qualified") for row in report["withdrawals"]) and len(report["withdrawals"]) == len(identifiers)
    except BaseException as error:
        report["infrastructure_error"] = {"type": type(error).__name__, "message": str(error)}
        report["ok"] = False
        if not isinstance(error, (KeyboardInterrupt, SystemExit)):
            traceback.print_exc()
    finally:
        # Restore all original critical bytes in the private tree, even after
        # an interrupted compiler/test or an unsuccessful individual mutation.
        restored = {}
        for rel, data in originals.items():
            target = private / rel
            if target.is_file():
                if target.read_bytes() != data:
                    target.write_bytes(data)
                restored[rel] = target.read_bytes() == data
            else:
                restored[rel] = False
        report["private_bytes_restored"] = restored
        if not all(restored.values()):
            report["ok"] = False
        save()
    print(json.dumps({"schema": SCHEMA, "official_receipt": False, "ok": report["ok"],
                      "report": str(report_path)}, ensure_ascii=False), flush=True)
    return 0 if report["ok"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--list", action="store_true", help="List only; this is also the default.")
    selection.add_argument("--only", action="append", choices=tuple(WITHDRAWALS), help="Run only this named withdrawal; repeat to select several.")
    selection.add_argument("--all", action="store_true", help="Explicitly run all six expensive native withdrawals.")
    parser.add_argument("--source", type=Path, default=ROOT, help="Read-only source checkout to copy.")
    parser.add_argument("--out", type=Path, help="Required external directory for logs, private sources and nonofficial report.")
    parser.add_argument("--build-timeout", type=int, default=360)
    parser.add_argument("--test-timeout", type=int, default=60)
    parser.add_argument("--worker", choices=("build", "test"), help=argparse.SUPPRESS)
    parser.add_argument("--worker-case", choices=tuple(WITHDRAWALS), help=argparse.SUPPRESS)
    parser.add_argument("--binary-dir", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        if not args.worker_case or not args.binary_dir:
            parser.error("private worker requires its case and binary directory")
        return worker(args.worker, args.worker_case, args.binary_dir)
    if not 1 <= args.build_timeout <= 360 or not 1 <= args.test_timeout <= 60:
        parser.error("build timeout must be 1..360 seconds and test timeout 1..60 seconds")
    if args.list or not (args.only or args.all):
        print(json.dumps({"schema": SCHEMA, "will_build": False, "official_receipt": False,
                          "withdrawals": [{"id": key, "source": spec["source"], "test_id": test_id(spec),
                                           "marker": spec["marker"], "meaning": spec["meaning"]}
                                          for key, spec in WITHDRAWALS.items()]}, ensure_ascii=False, indent=2))
        return 0
    if args.out is None:
        parser.error("execution requires --out outside the source checkout")
    if hasattr(signal, "SIGTERM"):
        def stop(_signum, _frame):
            raise KeyboardInterrupt("R03R_WITHDRAWAL_TERMINATED")
        signal.signal(signal.SIGTERM, stop)
    identifiers = list(WITHDRAWALS) if args.all else list(dict.fromkeys(args.only))
    return supervise(identifiers, args.source, args.out, args.build_timeout, args.test_timeout)


if __name__ == "__main__":
    raise SystemExit(main())
