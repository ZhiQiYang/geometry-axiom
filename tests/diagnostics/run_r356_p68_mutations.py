#!/usr/bin/env python3
"""Run four named P68/legacy-field retractions with the original judges.

  GEOMETRY_CHROME=/path/to/chrome python3 -B \
    tests/diagnostics/run_r356_p68_mutations.py \
    --output /tmp/r356-p68-receipts-NEW --binary-dir /tmp/r356-p68-binaries

Run alone in this checkout. Each target is backed up and atomically restored
byte for byte; concurrent edits are never overwritten. Browser phases own a
fresh service, port, CDP port, profile and feedback directory. The original
P68 throwOnFail stops at its named assertion: only that exact fatal, after the
26 unchanged passing assertions, counts as a kill. A timeout, transport/network
failure, browser exception, skip, different assertion or process crash does not.
Node phases run the unchanged six-test suite with its TAP reporter. Each mutant
must have five passes and one designated ERR_ASSERTION; restoration repeats all
six passes. This is diagnostic evidence, not full canvas or mutation-ledger
evidence. No golden, expected count, assertion or ledger is written.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SELF = "tests/diagnostics/run_r356_p68_mutations.py"
HELPER = "tests/diagnostics/run_r356_editor_mutations.py"
spec = importlib.util.spec_from_file_location("r356_p68_helpers", ROOT / HELPER)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
require, digest, fingerprints = helper.require, helper.digest, helper.fingerprints
write_json, git = helper.write_json, helper.git
P68_ASSERTION = "P68 邊界定位：只改A/B保留同ID及完整定位定義"
PRIORITY_GUARD = "      if(input.Role==='custom' && (input.Role!==old.definition.role || priorityEdited)){"
NODE_NAMES = (
    "R11-UI-U64: catalog numbers never round the exact timber revision",
    "R11-UI-ELIGIBILITY: owner, groups and unknown qualification reject the whole copy",
    "R11-UI-PRIORITY: full int64 text is authoritative and unsafe legacy projections are rejected",
    "R11-UI-ORDER: a late read cannot authorize a reordered selection",
    "R11-UI-RECIPE-LIFETIME: pan and zoom preserve recipes, frame and revision changes expire them",
    "R11-UI-INPUT-IME: text and composition shortcuts never reach geometry copy",
)
MUTATIONS = (
    {"name": "M356_P68_CONFIRM_DISPATCH_REMOVE", "suite": "p68",
     "target": "geometry-web/project_audit_test.js", "assertion": P68_ASSERTION,
     "before": "    await ctl(editor.confirm);await settleTimberImpact();\n", "after": ""},
    {"name": "M356_LEGACY_PRIORITY_VALIDATION_REMOVE", "suite": "node",
     "target": "geometry-web/timber-edit.js", "assertion": "R356_LEGACY_Pri_INVALID_MARK",
     "before": PRIORITY_GUARD, "after": "      if(false){"},
    {"name": "M356_LEGACY_DIMENSION_VALIDATION_REMOVE", "suite": "node",
     "target": "geometry-web/timber-edit.js", "assertion": "R356_LEGACY_A_INVALID_MARK",
     "before": "      if(invalidDimensions.length){", "after": "      if(false){"},
    {"name": "M356_LEGACY_UNEDITED_PRIORITY_PROJECTED", "suite": "node",
     "target": "geometry-web/timber-edit.js", "assertion": "R356_LEGACY_EXACT_PRIORITY_HANDOFF",
     "before": PRIORITY_GUARD, "after": PRIORITY_GUARD.replace("|| priorityEdited", "|| true")},
)
SOURCE_FILES = tuple(dict.fromkeys((*helper.SOURCE_FILES, SELF, HELPER,
    "geometry-web/project_audit_test.js", "geometry-web/serve.py",
    "tests/test_timber_edit_ui.js", "tests/run_all.expected.json", "tests/mutants_results.json")))


def environment(temporary, folder, browser):
    if browser:
        env, port = helper.effective_environment(temporary, folder, "p68")
        del env["GEOMETRY_CDP_FROM_P31"]
        env["GEOMETRY_PROJECT_AUDIT_ONLY"] = "1"
        env["GEOMETRY_PROJECT_AUDIT_SCREENSHOT_DIR"] = str(folder / "screens")
    else:
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(("GEOMETRY_", "MUTATE_"))}
        port = None
    # Node injection/filter/reporter overrides must not replace the real judge.
    env = {key: value for key, value in env.items()
           if key != "NODE_OPTIONS" and not key.startswith("NODE_TEST_")}
    return env, port


def run_phase(mutation, phase, output, args, runtime):
    folder = output / mutation["name"] / phase
    folder.mkdir()
    print(mutation["name"] + " " + phase + " -> " + str(folder), flush=True)
    started = time.monotonic()
    record = {"name": mutation["name"], "phase": phase, "suite": mutation["suite"],
              "cwd": str(ROOT), "head": git("rev-parse", "HEAD"),
              "sourceBefore": fingerprints(SOURCE_FILES), "returncode": None}
    server = driver = None
    browser = mutation["suite"] == "p68"
    try:
        with tempfile.TemporaryDirectory(prefix="r356-p68-") as temporary_name:
            env, port = environment(Path(temporary_name), folder, browser)
            command = [args.node, "geometry-web/cdp_test.js"] if browser else [
                args.node, "--test", "--test-reporter=tap", "tests/test_timber_edit_ui.js"]
            record.update(testCommand=command, environment=helper.recorded_environment(env))
            if browser:
                server_command = [sys.executable, "-B", "-u", "geometry-web/start_local.py",
                                  "--port", str(port), "--binary-dir", str(args.binary_dir)]
                version = runtime.source_version(ROOT)
                record.update(serverCommand=server_command, expectedRuntimeVersion=version)
            write_json(folder / "launch.json", record)
            with (folder / "stdout.log").open("xb") as stdout, (folder / "stderr.log").open("xb") as stderr:
                try:
                    if browser:
                        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                        with (folder / "server.log").open("xb") as server_log:
                            server = subprocess.Popen(server_command, cwd=ROOT, env=env, stdout=server_log,
                                                      stderr=subprocess.STDOUT, start_new_session=True)
                        record["serverPid"] = server.pid
                        deadline = time.monotonic() + args.startup_timeout
                        while True:
                            require(server.poll() is None, "isolated server exited during startup")
                            try:
                                record["runtimeBefore"] = helper.runtime_status(opener, env["GEOMETRY_TEST_URL"], version)
                                break
                            except (urllib.error.URLError, TimeoutError, ConnectionError):
                                require(time.monotonic() < deadline, "isolated server startup timed out")
                                time.sleep(0.2)
                    driver = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout,
                                              stderr=stderr, start_new_session=True)
                    record["driverPid"] = driver.pid
                    record["returncode"] = driver.wait(timeout=args.timeout)
                    if browser:
                        require(server.poll() is None, "isolated server exited during browser run")
                        record["runtimeAfter"] = helper.runtime_status(opener, env["GEOMETRY_TEST_URL"], version)
                finally:
                    try:
                        helper.stop_owned(driver)
                    finally:
                        helper.stop_owned(server)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        record["infrastructureError"] = f"{type(error).__name__}: {error}"
    finally:
        record["seconds"] = round(time.monotonic() - started, 3)
        record["sourceAfter"] = fingerprints(SOURCE_FILES)
        if record["sourceAfter"] != record["sourceBefore"]:
            record["infrastructureError"] = "source, original judge, runner, golden, expected or ledger changed during phase"
        record["logs"] = {name: digest((folder / name).read_bytes())
                          for name in ("stdout.log", "stderr.log", "server.log") if (folder / name).exists()}
        write_json(folder / "receipt.json", record)
    return record, folder


def judge_browser(record, text, mutation, phase, baseline):
    failed = phase == "mutant"
    results = helper.prefixed_json(text, "CDP_RESULT ")
    require(len(results) == 1, "exactly one original CDP_RESULT is required")
    result = results[0]
    require(result.get("schema") == "geometry-cdp-result/1", "unexpected CDP result schema")
    require(result.get("uncaughtBrowserExceptions") == 0 and result.get("unexpectedBrowserExceptions") == 0
            and result.get("skipped") == [] and "[SKIP]" not in text,
            "browser exceptions or skips cannot count as detection")
    require(result.get("firstTransportFailure") is None and result.get("apiTransportFailures") == []
            and result.get("apiTransportTraceComplete") is True and result.get("firstNetworkFailure") is None,
            "transport/network failures or incomplete transport trace cannot count as detection")
    scope, env = result.get("scope", {}), record["environment"]
    require(scope.get("mode") == "partial" and scope.get("filters") == ["GEOMETRY_PROJECT_AUDIT_ONLY"]
            and scope.get("modifiers") == [] and scope.get("browserProfile") == env["GEOMETRY_CHROME_PROFILE"]
            and scope.get("feedbackDirectory") == env["GEOMETRY_FEEDBACK_DIR"]
            and scope.get("cdpPort") == int(env["GEOMETRY_CDP_PORT"])
            and scope.get("url") == env["GEOMETRY_TEST_URL"], "P68 scope/profile/ports must belong to this phase")
    assertions = [{"name": match[1], "passed": match[2] == "✓", "detail": (match[3] or "").strip()}
                  for match in re.finditer(r"^(P68 .+?) ([✓✗])(?: (.*))?$", text, re.MULTILINE)]
    failures = [row for row in assertions if not row["passed"]]
    passed = sum(row["passed"] for row in assertions)
    require(passed == (26 if failed else 36) and result.get("passedAssertions") == passed
            and result.get("failedAssertions") == int(failed)
            and result.get("sections") == {"P68": passed} and result.get("sectionOrder") == ["P68"]
            and result.get("sectionsFailed", {}) == ({"P68": 1} if failed else {}),
            "P68 exact original counts/sections must agree with the assertion log")
    require([row["name"] for row in failures] == ([mutation["assertion"]] if failed else []),
            "only the designated P68 assertion may fail")
    fatal_lines = re.findall(r"^FATAL: (.+)$", text, re.MULTILINE)
    if failed:
        fatal = "P68 assertion failed: " + mutation["assertion"].removeprefix("P68 ") + " " + failures[0]["detail"]
        require(result.get("completed") is False and result.get("fatal") == fatal and fatal_lines == [fatal]
                and result.get("currentSection") == "P68"
                and result.get("goldenCompare") == "not compared (run did not complete)",
                "only the original throwOnFail for the designated assertion is an accepted fatal")
        require(helper.prefixed_json(text, "FATAL_NETWORK: ") == [{"failures": [], "pendingAssets": []}]
                and "FATAL_CAPTURE_FAILED:" not in text, "fatal must not conceal network or capture failure")
        require(baseline is not None and assertions[:26] == baseline["assertions"][:26]
                and baseline["assertions"][26]["name"] == mutation["assertion"],
                "mutant must preserve the original 26 passing assertions and fail exactly the next one")
    else:
        require(result.get("completed") is True and "fatal" not in result and not fatal_lines
                and result.get("goldenCompare") == "not compared (partial mode)", "original P68 did not complete")
    # Passing details can contain before/after counters; retain every row and
    # demand byte-equivalent verdict/name/detail sequences after restoration.
    if phase == "restored":
        require(assertions == baseline["assertions"], "restored P68 must repeat all original assertions")
    return {"result": result, "assertions": assertions}


def judge_node(text, mutation, phase, baseline):
    failed = phase == "mutant"
    require(text.startswith("TAP version 13\n") and "Bail out!" not in text
            and not re.search(r"^(?:ok|not ok) \d+ - .+ #\s*(SKIP|TODO)\b", text, re.IGNORECASE | re.MULTILINE),
            "expected normal TAP without skip/todo directives or bailout")
    rows = [{"passed": match[1] == "ok", "number": int(match[2]), "name": match[3]}
            for match in re.finditer(r"^(ok|not ok) (\d+) - (.+)$", text, re.MULTILINE)]
    require([row["number"] for row in rows] == list(range(1, 7))
            and [row["name"] for row in rows] == list(NODE_NAMES), "all six original Node tests must execute in order")
    summary = {}
    for key in ("tests", "suites", "pass", "fail", "cancelled", "skipped", "todo"):
        values = re.findall(r"^# " + key + r" (\d+)$", text, re.MULTILINE)
        require(len(values) == 1, "missing/duplicate TAP summary: " + key)
        summary[key] = int(values[0])
    require(summary == {"tests": 6, "suites": 0, "pass": 5 if failed else 6,
                        "fail": int(failed), "cancelled": 0, "skipped": 0, "todo": 0},
            "Node suite counts must be exactly 6/0 or 5/1 with zero skips/cancellation")
    failures = [row for row in rows if not row["passed"]]
    require([row["name"] for row in failures] == ([NODE_NAMES[2]] if failed else []),
            "only the original priority/legacy validation test may fail")
    codes = re.findall(r"^  code: ['\"]?([^'\"\n]+)['\"]?$", text, re.MULTILINE)
    require(codes == (["ERR_ASSERTION"] if failed else []), "only one normal ERR_ASSERTION may count as killed")
    if failed:
        require(re.findall(r"^  failureType: ['\"]?([^'\"\n]+)['\"]?$", text, re.MULTILINE) == ["testCodeFailure"]
                and re.findall(r"^  name: ['\"]?([^'\"\n]+)['\"]?$", text, re.MULTILINE) == ["AssertionError"],
                "crash/process/reporter failures cannot count as a Node assertion kill")
        markers = re.findall(r"R356_LEGACY_[A-Za-z0-9_]+", text)
        require(markers == [mutation["assertion"]], "the sole Node error must name the designated legacy assertion")
        require(baseline is not None and [row["name"] for row in rows] == [row["name"] for row in baseline["tests"]],
                "mutant must retain the baseline test sequence")
    if phase == "restored":
        require(rows == baseline["tests"], "restored Node run must repeat all original tests")
    return {"tests": rows, "summary": summary}


def judge(record, folder, mutation, phase, baseline=None):
    require(not record.get("infrastructureError"), record.get("infrastructureError", ""))
    require(record["returncode"] == int(phase == "mutant"), "unexpected exit; crash/error is not a mutation kill")
    text = (folder / "stdout.log").read_text(encoding="utf-8")
    if mutation["suite"] == "node":
        require((folder / "stderr.log").read_bytes() == b"", "Node stderr must be empty; errors belong to the original TAP")
        value = judge_node(text, mutation, phase, baseline)
    else:
        value = judge_browser(record, text, mutation, phase, baseline)
    return {"returncode": record["returncode"], "receipt": str(folder / "receipt.json"),
            "designatedAssertion": mutation["assertion"], **value}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True, help="new evidence directory; existing paths are refused")
    parser.add_argument("--binary-dir", type=Path, required=True, help="dedicated absolute directory under TEMP")
    parser.add_argument("--mutation", action="append", choices=[row["name"] for row in MUTATIONS])
    parser.add_argument("--timeout", type=float, default=300, help="phase process limit; original assertion polling is unchanged")
    parser.add_argument("--startup-timeout", type=float, default=180)
    args = parser.parse_args()
    require(sys.platform.startswith("linux"), "start_local.py requires Linux")
    require(args.timeout > 0 and args.startup_timeout > 0, "timeouts must be positive")
    require(Path(git("rev-parse", "--show-toplevel")).resolve() == ROOT, "runner must remain in this repository")
    require(os.environ.get("GEOMETRY_CHROME"), "set GEOMETRY_CHROME to the intended executable")
    chrome, args.node = shutil.which(os.environ["GEOMETRY_CHROME"]), shutil.which("node")
    require(chrome is not None and args.node is not None, "configured Chrome and Node must be executable")
    launcher = helper.module_at("r356_p68_start_local", "geometry-web/start_local.py")
    args.binary_dir = launcher.binary_directory(args.binary_dir)
    launcher.ensure_stack()
    runtime = helper.module_at("r356_p68_runtime", "geometry-web/runtime_version.py")
    chosen = [row for row in MUTATIONS if not args.mutation or row["name"] in args.mutation]
    require(not args.mutation or len(args.mutation) == len(chosen), "duplicate mutation selections are refused")
    output = args.output.resolve()
    require(output != ROOT and ROOT not in output.parents, "keep receipts outside the source checkout")
    output.mkdir(parents=True, exist_ok=False)
    initial = fingerprints(SOURCE_FILES)
    report = {"schema": "r356-p68-legacy-mutations/1", "root": str(ROOT), "head": git("rev-parse", "HEAD"),
              "baseSources": initial, "rows": [], "status": "blocked",
              "coverage": "Original P68 and six Node UI contract tests only; no full/shard or ledger credit.",
              "tools": {name: {"path": path, **digest(Path(path).read_bytes())}
                        for name, path in (("python", sys.executable), ("node", args.node), ("chrome", chrome))}}
    # Share the existing editor runner's lock: both temporarily edit this tree.
    lock = Path(tempfile.gettempdir()) / ("geometry-r356-editor-" + hashlib.sha256(str(ROOT).encode()).hexdigest()[:20] + ".lock")
    lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(lock_fd, "w", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid(), "root": str(ROOT), "output": str(output)}, stream)

    def interrupted(signum, _frame):
        raise KeyboardInterrupt(f"signal {signum}")

    previous_sigterm = signal.signal(signal.SIGTERM, interrupted)
    try:
        write_json(output / "start.json", report)
        for mutation in chosen:
            require(fingerprints(SOURCE_FILES) == initial, "checkout changed outside runner; refusing mutation")
            target = ROOT / mutation["target"]
            original = target.read_bytes()
            before, after = mutation["before"].encode(), mutation["after"].encode()
            require(original.count(before) == 1, "mutation anchor must occur exactly once: " + mutation["name"])
            mutated = original.replace(before, after, 1)
            case_dir = output / mutation["name"]
            case_dir.mkdir()
            with (case_dir / "original.bin").open("xb") as stream:
                stream.write(original)
            row = {**mutation, "original": digest(original), "mutated": digest(mutated), "phases": {}}
            report["rows"].append(row)
            record, folder = run_phase(mutation, "baseline", output, args, runtime)
            baseline = row["phases"]["baseline"] = judge(record, folder, mutation, "baseline")
            require(fingerprints(SOURCE_FILES) == initial, "checkout changed before mutation; refusing overwrite")
            mutant_error = None
            try:
                helper.replace_target(target, original, mutated)
                record, folder = run_phase(mutation, "mutant", output, args, runtime)
                try:
                    row["phases"]["mutant"] = judge(record, folder, mutation, "mutant", baseline)
                except (RuntimeError, ValueError, KeyError) as error:
                    mutant_error = str(error)
                    row["phases"]["mutant"] = {"rejected": mutant_error, "receipt": str(folder / "receipt.json")}
            finally:
                current = target.read_bytes()
                require(current in (original, mutated), "concurrent target edit: not overwritten; backup is " + str(case_dir / "original.bin"))
                if current == mutated:
                    helper.replace_target(target, mutated, original)
                row["restoredBytesEqual"] = target.read_bytes() == original
            record, folder = run_phase(mutation, "restored", output, args, runtime)
            row["phases"]["restored"] = judge(record, folder, mutation, "restored", baseline)
            require(mutant_error is None, "named mutation was not killed: " + str(mutant_error))
            require(fingerprints(SOURCE_FILES) == initial, "all sources, judges, golden, expected and ledger must remain byte-identical")
            row["status"] = "killed"
            print(mutation["name"] + " baseline=0 mutant=1 restored=0", flush=True)
        report["status"] = "passed"
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        report["finalSources"] = fingerprints(SOURCE_FILES)
        report["sourcesRestored"] = report["finalSources"] == initial
        report["ledgerBytesUnchanged"] = report["finalSources"]["tests/mutants_results.json"] == initial["tests/mutants_results.json"]
        if not report["sourcesRestored"]:
            report["status"] = "blocked"
        write_json(output / "report.json", report)
        lock.unlink()
        signal.signal(signal.SIGTERM, previous_sigterm)
    print(json.dumps({"status": report["status"], "output": str(output), "error": report.get("error")}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"R356 P68 preflight refused: {error}", file=sys.stderr)
        raise SystemExit(2)
