#!/usr/bin/env python3
"""Reproduce two named editor-routing mutations with unchanged browser judges.

Requires Linux, Node with the original CDP driver's WebSocket support, and
GEOMETRY_CHROME (plus GEOMETRY_CHROME_FLAGS if required by that installation).
Run when no other test or editor is using this checkout: the two product files
are changed temporarily, with exact-byte backups and guarded restoration.

  python tests/diagnostics/run_r356_editor_mutations.py \
    --output /tmp/r356-editor-receipts-NEW \
    --binary-dir /tmp/r356-editor-binaries

The output directory must not exist. Each baseline/mutant/restored phase owns
a fresh server port, CDP port, profile, and feedback directory. Only a completed
run failing the designated assertion counts as killed. Errors, skips, transport
failures, process crashes, and runner timeouts do not. The original C10 judge's
SINGLE_NEW_FIELD_FORM assertion explicitly distinguishes a ready, idle product
with a missing form from an environment failure; its polling is not relaxed.

This is diagnostic evidence, not a full canvas/shard or mutation-ledger receipt.
No assertion, golden, or mutation ledger is written by this tool.
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
import socket
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
EXTRACTOR = "tests/diagnostics/r356_original_p64.cjs"
SELF = "tests/diagnostics/run_r356_editor_mutations.py"
T4 = "P64 T4 編輯角材聚焦且明示已帶入原定位引用"
SOURCE_FILES = (
    "geometry-web/app.js", "geometry-web/face-context-menu.js",
    "geometry-web/timber-edit.js", "geometry-web/reference-workspace.js",
    "geometry-web/context-menu-shell.js", "geometry-web/cdp_test.js",
    "geometry-web/timber_reuse_test.js", "geometry-web/cdp_helpers.js",
    "geometry-web/cdp_floor.js", "geometry-web/canvas_shards.js",
    "geometry-web/canvas_shards.json", "geometry-web/cdp_sections.golden.json",
    "geometry-web/transport_failure_trace.js", "geometry-web/start_local.py",
    "geometry-web/runtime_version.py", "tests/binaries.py", EXTRACTOR, SELF,
)
MUTATIONS = (
    {
        "name": "M356_SINGLE_EDITOR_TO_BATCH", "suite": "p64-through-t4",
        "target": "geometry-web/app.js", "assertion": T4,
        "before": "if (window.TimberEdit && (timberFields || fe.timberSelection.size > 1 || selected?.engineeringSources?.length)) {",
        "after": "if (window.TimberEdit) {",
    },
    {
        "name": "M356_MENU_FIELDS_DISPATCH_REMOVED", "suite": "p116-c10",
        "target": "geometry-web/face-context-menu.js", "assertion": "SINGLE_NEW_FIELD_FORM",
        "before": "await feRunAction(a.act,{timberFields:a.act==='edit'});",
        "after": "await feRunAction(a.act);",
    },
)
C10_REQUIRED = {
    "C10_IDS_ORDER_AND_PLACEMENTS_RETAINED", "C10_UNSELECTED_FIELDS_RETAINED",
    "C10_B_ONLY_SELECTED_TARGETS", "C10_SOURCES_UNCHANGED",
    "C10_NO_DELETE_RECREATE_OR_PER_OBJECT_COMMIT", "C10_ONE_HISTORY",
    "C10_PRIORITY_WIRE_IS_EXACT_STRING", "C10_PREVIEW_PRIORITY_TEXT_EXACT",
    "C10_NATIVE_PRIORITY_TEXT_EXACT", "C10_PRECISE_PRIORITY_ONE_HISTORY",
}


def digest(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def fingerprints(names):
    return {name: digest((ROOT / name).read_bytes()) for name in names}


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def replace_target(path, expected, replacement):
    """Replace one known version atomically; never truncate a live source file."""
    require(path.read_bytes() == expected, "concurrent source edit; refusing to replace " + str(path))
    mode = stat.S_IMODE(path.stat().st_mode)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".r356-editor-", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(replacement)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        require(path.read_bytes() == expected, "source changed while preparing replacement: " + str(path))
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def module_at(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def free_ports():
    # Reserve both at once so the two probes cannot select the same port.
    with socket.socket() as server, socket.socket() as browser:
        server.bind(("127.0.0.1", 0))
        browser.bind(("127.0.0.1", 0))
        return server.getsockname()[1], browser.getsockname()[1]


def stop_owned(process):
    """Only terminate the process group created by this runner."""
    if process is None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)


def effective_environment(temporary, output, suite):
    # Never inherit a partial filter, external test service, stale profile,
    # injected native executable, screenshot destination, or golden update.
    env = {name: value for name, value in os.environ.items()
           if not name.startswith(("GEOMETRY_", "MUTATE_"))}
    env["GEOMETRY_CHROME"] = os.environ["GEOMETRY_CHROME"]
    if "GEOMETRY_CHROME_FLAGS" in os.environ:
        env["GEOMETRY_CHROME_FLAGS"] = os.environ["GEOMETRY_CHROME_FLAGS"]
    port, cdp_port = free_ports()
    profile, feedback = temporary / "profile", temporary / "feedback"
    profile.mkdir()
    feedback.mkdir()
    env.update(GEOMETRY_CHROME_PROFILE=str(profile),
               GEOMETRY_FEEDBACK_DIR=str(feedback),
               GEOMETRY_REPAIR_SCREENSHOT_DIR=str(output / "screens"),
               GEOMETRY_CDP_PORT=str(cdp_port),
               GEOMETRY_TEST_URL=f"http://127.0.0.1:{port}/")
    if suite == "p116-c10":
        env.update(GEOMETRY_TIMBER_REUSE_ONLY="1", GEOMETRY_TIMBER_REUSE_CASE="C10")
    else:
        env["GEOMETRY_CDP_FROM_P31"] = "1"
    return env, port


def recorded_environment(env):
    names = {"PATH", "PYTHONPATH", "NODE_PATH", "CC", "CFLAGS", "CPPFLAGS",
             "LDFLAGS", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP"}
    return {key: value for key, value in sorted(env.items())
            if key.startswith("GEOMETRY_") or key in names}


def runtime_status(opener, url, expected_version):
    with opener.open(url + "runtime", timeout=2) as response:
        value = json.load(response)
    require(value.get("schema") == "geometry-runtime/1" and value.get("fresh") is True
            and value.get("version") == expected_version
            and Path(value.get("root", "")).resolve() == ROOT,
            "runtime must prove fresh sources and this exact repository")
    return value


def run_phase(mutation, phase, output, args, names, runtime_module):
    folder = output / mutation["name"] / phase
    folder.mkdir(parents=True, exist_ok=False)
    print(mutation["name"] + " " + phase + " -> " + str(folder), flush=True)
    started = time.monotonic()
    record = {"name": mutation["name"], "phase": phase, "suite": mutation["suite"],
              "cwd": str(ROOT), "head": git("rev-parse", "HEAD"),
              "sourceBefore": fingerprints(names), "returncode": None}
    server = browser = None
    try:
        with tempfile.TemporaryDirectory(prefix="r356-editor-") as temporary_name:
            temporary = Path(temporary_name)
            env, port = effective_environment(temporary, folder, mutation["suite"])
            server_command = [sys.executable, "-B", "-u", "geometry-web/start_local.py",
                              "--port", str(port), "--binary-dir", str(args.binary_dir)]
            test_command = [args.node, "geometry-web/cdp_test.js"] if mutation["suite"] == "p116-c10" else [
                args.node, EXTRACTOR, "--through-t4"]
            expected_version = runtime_module.source_version(ROOT)
            record.update(serverCommand=server_command, testCommand=test_command,
                          environment=recorded_environment(env), expectedRuntimeVersion=expected_version)
            write_json(folder / "launch.json", record)
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with (folder / "server.log").open("xb") as server_log, (folder / "browser.log").open("xb") as browser_log:
                try:
                    server = subprocess.Popen(server_command, cwd=ROOT, env=env, stdout=server_log,
                                              stderr=subprocess.STDOUT, start_new_session=True)
                    record["serverPid"] = server.pid
                    deadline = time.monotonic() + args.startup_timeout
                    while True:
                        require(server.poll() is None, "isolated server exited during startup")
                        try:
                            record["runtimeBefore"] = runtime_status(opener, env["GEOMETRY_TEST_URL"], expected_version)
                            break
                        except (urllib.error.URLError, TimeoutError, ConnectionError):
                            require(time.monotonic() < deadline, "isolated server startup timed out")
                            time.sleep(0.2)
                    browser = subprocess.Popen(test_command, cwd=ROOT, env=env, stdout=browser_log,
                                               stderr=subprocess.STDOUT, start_new_session=True)
                    record["driverPid"] = browser.pid
                    record["returncode"] = browser.wait(timeout=args.timeout)
                    require(server.poll() is None, "isolated server exited during browser run")
                    record["runtimeAfter"] = runtime_status(opener, env["GEOMETRY_TEST_URL"], expected_version)
                finally:
                    try:
                        stop_owned(browser)
                    finally:
                        stop_owned(server)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        record["infrastructureError"] = f"{type(error).__name__}: {error}"
    finally:
        record["seconds"] = round(time.monotonic() - started, 3)
        record["sourceAfter"] = fingerprints(names)
        if record["sourceAfter"] != record["sourceBefore"]:
            record["infrastructureError"] = "source, original judge, golden, or ledger changed during phase"
        record["logs"] = {name: digest((folder / name).read_bytes()) for name in ("server.log", "browser.log")
                          if (folder / name).exists()}
        write_json(folder / "receipt.json", record)
    return record, folder


def prefixed_json(text, prefix):
    return [json.loads(line[len(prefix):]) for line in text.splitlines() if line.startswith(prefix)]


def judge(record, folder, mutation, phase, baseline=None):
    expected_failure = int(phase == "mutant")
    require(not record.get("infrastructureError"), record.get("infrastructureError", ""))
    require(record["returncode"] == expected_failure, "unexpected process exit; cannot count a crash/error as killed")
    text = (folder / "browser.log").read_text(encoding="utf-8")
    results = prefixed_json(text, "CDP_RESULT ")
    require(len(results) == 1, "exactly one original CDP result is required")
    result = results[0]
    require(result.get("schema") == "geometry-cdp-result/1" and result.get("completed") is True
            and "fatal" not in result, "original browser judge did not complete")
    require(result.get("unexpectedBrowserExceptions") == 0 and result.get("uncaughtBrowserExceptions") == 0
            and result.get("skipped") == [] and "[SKIP]" not in text,
            "exceptions or skips cannot count as mutation detection")
    require(result.get("firstTransportFailure") is None and result.get("apiTransportFailures") == []
            and result.get("apiTransportTraceComplete") is True and result.get("firstNetworkFailure") is None,
            "transport/network failures or incomplete transport trace cannot count as killed")
    env, scope = record["environment"], result.get("scope", {})
    flag = "GEOMETRY_TIMBER_REUSE_ONLY" if mutation["suite"] == "p116-c10" else "GEOMETRY_CDP_FROM_P31"
    require(scope.get("mode") == "partial" and scope.get("filters") == [flag] and scope.get("modifiers") == []
            and scope.get("browserProfile") == env["GEOMETRY_CHROME_PROFILE"]
            and scope.get("feedbackDirectory") == env["GEOMETRY_FEEDBACK_DIR"]
            and scope.get("cdpPort") == int(env["GEOMETRY_CDP_PORT"])
            and scope.get("url") == env["GEOMETRY_TEST_URL"], "scope/profile/port must belong to this phase")
    require(result.get("goldenCompare") == "not compared (partial mode)", "diagnostic must not claim or update golden")
    prefix = "R116" if mutation["suite"] == "p116-c10" else "P64"
    assertions = [{"name": match[1], "passed": match[2] == "✓"}
                  for match in re.finditer(r"^(" + prefix + r" .+?) ([✓✗])(?: |$)", text, re.MULTILINE)]
    failures = [row["name"] for row in assertions if not row["passed"]]
    section = "P116" if mutation["suite"] == "p116-c10" else "P64"
    passed = sum(row["passed"] for row in assertions)
    require(result.get("passedAssertions") == passed and result.get("failedAssertions") == expected_failure
            and result.get("sections") == {section: passed} and result.get("sectionOrder") == [section]
            and result.get("sectionsFailed", {}) == ({section: 1} if expected_failure else {}),
            "exact assertion totals and section ownership must agree with original log")
    expected_name = mutation["assertion"] if section == "P64" else "R116 " + mutation["assertion"]
    require(failures == ([expected_name] if expected_failure else []), "only the designated assertion may fail")
    cases = prefixed_json(text, "R116_CASE_RESULT ")
    if section == "P64":
        require(passed == 18 - expected_failure and not cases, "P64 through T4 must execute all 18 original assertions")
        manifests = prefixed_json(text, "R356_P64_DIAGNOSTIC ")
        require(len(manifests) == 1 and manifests[0]["expectedAssertions"] == 18
                and manifests[0]["driverBytes"] == record["sourceBefore"]["geometry-web/cdp_test.js"],
                "P64 must come from the fingerprinted original driver")
    else:
        require(len(cases) == 1 and cases[0].get("id") == "C10", "only original C10 may execute")
        case = cases[0]
        if expected_failure:
            require(case.get("status") == "fail" and case.get("kind") == "assertion"
                    and case.get("assertion") == "SINGLE_NEW_FIELD_FORM" and passed == 16,
                    "C10 removal must reach exactly the named product-form assertion after 16 passes")
            require(baseline is not None and assertions[:-1] == baseline["assertions"][:16],
                    "mutant must preserve the exact C10 passing prefix")
        else:
            require(case.get("status") == "pass" and case.get("kind") is None
                    and case.get("assertion") is None and case.get("error") is None,
                    "original C10 must pass without precondition/cleanup/errors")
            names = {row["name"].removeprefix("R116 ") for row in assertions}
            require(C10_REQUIRED <= names, "C10 must retain sources, in-place identity/history, and exact-priority assertions")
    value = {"returncode": record["returncode"], "result": result, "cases": cases,
             "assertions": assertions, "designatedAssertion": mutation["assertion"]}
    if phase == "restored":
        require(baseline is not None and assertions == baseline["assertions"],
                "restored run must repeat every baseline assertion in the same order")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True, help="new evidence directory; existing paths are refused")
    parser.add_argument("--binary-dir", type=Path, required=True, help="dedicated absolute directory under TEMP")
    parser.add_argument("--mutation", action="append", choices=[m["name"] for m in MUTATIONS],
                        help="default: both named mutations, sequentially")
    parser.add_argument("--timeout", type=float, default=180, help="browser process deadline; never alters assertion polling")
    parser.add_argument("--startup-timeout", type=float, default=180)
    args = parser.parse_args()
    require(sys.platform.startswith("linux"), "start_local.py requires Linux")
    require(args.timeout > 0 and args.startup_timeout > 0, "timeouts must be positive")
    require(Path(git("rev-parse", "--show-toplevel")).resolve() == ROOT, "diagnostics must remain in the repository")
    require(os.environ.get("GEOMETRY_CHROME"), "set GEOMETRY_CHROME to the intended browser executable")
    chrome = shutil.which(os.environ["GEOMETRY_CHROME"])
    args.node = shutil.which("node")
    require(chrome is not None and args.node is not None, "configured Chrome and Node must be executable")
    launcher = module_at("r356_start_local", "geometry-web/start_local.py")
    args.binary_dir = launcher.binary_directory(args.binary_dir)
    launcher.ensure_stack()
    runtime = module_at("r356_runtime", "geometry-web/runtime_version.py")
    output = args.output.resolve()
    require(output != ROOT and ROOT not in output.parents, "keep diagnostic evidence outside the source checkout")
    output.mkdir(parents=True, exist_ok=False)
    chosen = [m for m in MUTATIONS if not args.mutation or m["name"] in args.mutation]
    require(not args.mutation or len(args.mutation) == len(chosen), "duplicate mutation selections are refused")
    # This file is only fingerprinted. It is never opened for writing or updated.
    ledger = "tests/mutants_results.json"
    names = (*SOURCE_FILES, ledger)
    before_all = fingerprints(names)
    report = {"schema": "r356-editor-routing-mutations/1", "root": str(ROOT),
              "head": git("rev-parse", "HEAD"), "baseSources": before_all,
              "tools": {name: {"path": path, **digest(Path(path).read_bytes())}
                        for name, path in (("python", sys.executable), ("node", args.node), ("chrome", chrome))},
              "coverage": "Original P64 through T4 and original P116 C10 only; no full/shard or mutation-ledger credit.",
              "rows": [], "status": "blocked"}
    lock = Path(tempfile.gettempdir()) / ("geometry-r356-editor-" + hashlib.sha256(str(ROOT).encode()).hexdigest()[:20] + ".lock")
    lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.write(lock_fd, json.dumps({"pid": os.getpid(), "root": str(ROOT), "output": str(output)}).encode())
    os.close(lock_fd)
    def interrupted(signum, _frame):
        raise KeyboardInterrupt(f"signal {signum}")
    previous_sigterm = signal.signal(signal.SIGTERM, interrupted)
    try:
        write_json(output / "start.json", report)
        for mutation in chosen:
            require(fingerprints(names) == before_all, "checkout changed outside this runner; refusing to overwrite it")
            target = ROOT / mutation["target"]
            original = target.read_bytes()
            before, after = mutation["before"].encode(), mutation["after"].encode()
            require(original.count(before) == 1, "exact mutation anchor must occur once: " + mutation["name"])
            mutated = original.replace(before, after, 1)
            case_dir = output / mutation["name"]
            case_dir.mkdir()
            with (case_dir / "original.bin").open("xb") as backup:
                backup.write(original)
            row = {**mutation, "original": digest(original), "mutated": digest(mutated), "phases": {}}
            report["rows"].append(row)
            baseline_record, folder = run_phase(mutation, "baseline", output, args, names, runtime)
            baseline = judge(baseline_record, folder, mutation, "baseline")
            row["phases"]["baseline"] = baseline
            require(fingerprints(names) == before_all, "checkout changed before mutation; refusing to overwrite it")
            mutant_error = None
            try:
                replace_target(target, original, mutated)
                record, folder = run_phase(mutation, "mutant", output, args, names, runtime)
                try:
                    row["phases"]["mutant"] = judge(record, folder, mutation, "mutant", baseline)
                except (RuntimeError, ValueError, KeyError) as error:
                    mutant_error = str(error)
                    row["phases"]["mutant"] = {"rejected": mutant_error, "receipt": str(folder / "receipt.json")}
            finally:
                current = target.read_bytes()
                require(current in (original, mutated),
                        "concurrent target edit detected: not overwritten; exact backup is " + str(case_dir / "original.bin"))
                if current == mutated:
                    replace_target(target, mutated, original)
                row["restoredBytesEqual"] = target.read_bytes() == original
            restored_record, folder = run_phase(mutation, "restored", output, args, names, runtime)
            row["phases"]["restored"] = judge(restored_record, folder, mutation, "restored", baseline)
            require(mutant_error is None, "named mutation was not killed: " + str(mutant_error))
            require(fingerprints(names) == before_all, "original judges, golden, ledger, and sources must remain byte-identical")
            row["status"] = "killed"
            print(mutation["name"] + " baseline=0 mutant=1 restored=0", flush=True)
        report["status"] = "passed"
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        report["finalSources"] = fingerprints(names)
        report["sourcesRestored"] = report["finalSources"] == before_all
        report["ledgerBytesUnchanged"] = report["finalSources"][ledger] == before_all[ledger]
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
        print(f"R356 preflight refused: {error}", file=sys.stderr)
        raise SystemExit(2)
