#!/usr/bin/env python3
"""Frozen-copy R12 browser evidence and named source withdrawals.

Every execution owns a fresh local service, native bridge, Chrome profile and
output directory. It runs the repository's actual space_model_test.js with
GEOMETRY_SPACE_PROFILE_ONLY=1. No golden or official mutation ledger is written.
Browser startup errors, timeouts, skips, missing reports and unrelated failures
are blocked evidence; only a named product assertion can kill a withdrawal.

Usage: python3 tests/r12_browser_evidence.py --out /absolute/new/directory
       python3 tests/r12_browser_evidence.py --out /absolute/new/directory --withdrawals
       python3 tests/r12_browser_evidence.py --preflight
GEOMETRY_CHROME must identify the installed browser. No sandbox flags are added.
The existing 35-minute browser job ceiling is retained for each execution.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 2100
EXPECTED = 60
SPARSE_ARCHIVE_PREFIXES = ("evidence/", "tests/evidence/", "tests/release-evidence/")
GENERIC_FAILURES = {"complete browser flow", "space group completeness"}
CASES = (
    ("R12-B01-visible-space-entry", "geometry-web/app.js",
     'faceWorkspace && s ? `<button type="button" class="btn wide" data-fp-build="${bid}"',
     'faceWorkspace && s ? `<button type="button" class="btn wide" data-r12-withdrawn-build="${bid}"',
     "R12_SPACE_ENTRY"),
    ("R12-B02-source-renders-candidates", "geometry-web/space-workspace.js",
     "renderTimberCandidates(source);renderProfileCandidates(source);",
     "renderTimberCandidates(source); /* withdrawn: admitted source profile controls */",
     "R12_ALL_WORLD_CANDIDATES"),
    ("R12-B03-no-default-selection", "geometry-web/space-workspace.js",
     '<input type="checkbox" data-sm-profile-run="${esc(run.id)}">',
     '<input type="checkbox" data-sm-profile-run="${esc(run.id)}" checked>',
     "R12_EXPLICIT_SELECTION"),
    ("R12-B04-shared-material-switch", "geometry-web/model-viewer.js",
     "if(visibility.timbers!==false)for(const object of result.profile_runs?.derived?.objects||[])if(object.role==='geometry')objects.push({...object,color:'#ab865f',opacity:1,label:'斷面拉伸件'});",
     "/* withdrawn: selected profile material meshes */",
     "R12_SHARED_MATERIAL_SWITCH"),
    ("R12-B05-overlap-notice", "geometry-web/space-workspace.js",
     "。未扣拉伸件間重疊，不含角材與牆；參考包絡不計材料，原位置不隨牆高改變。",
     "。不含角材與牆；參考包絡不計材料，原位置不隨牆高改變。",
     "R12_MATERIAL_NOTICE"),
    ("R12-B06-update-candidate-entry", "geometry-web/model-update-app.js",
     "$('muProfiles').innerHTML = current.profileRuns.map(",
     "$('muProfiles').innerHTML = [].map(",
     "R12_UPDATE_EXPLICIT_CANDIDATES"),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_files(root):
    result = subprocess.run(["git", "ls-files", "-c", "-o", "--exclude-standard", "-z"],
                            cwd=root, check=True, capture_output=True)
    return sorted({name.decode() for name in result.stdout.split(b"\0") if name})


def sparse_archives(root):
    """Record absent archival evidence, never omit an application/test source.

    This checkout can leave historical receipts sparse. The runtime identity,
    native registry and this browser group do not consume these archives.
    Keep their exact index blobs in a separate receipt instead of silently
    dropping missing paths or fetching gigabytes of unrelated past artifacts.
    """
    flags = subprocess.check_output(["git", "ls-files", "-v", "-z"], cwd=root)
    sparse = {row[2:].decode() for row in flags.split(b"\0") if row[:1].upper() == b"S"}
    missing = {name for name in sparse if not (root / name).exists()}
    unexpected = [name for name in missing if not name.startswith(SPARSE_ARCHIVE_PREFIXES)]
    if unexpected:
        raise RuntimeError("Sparse source must be materialized before evidence: " + sorted(unexpected)[0])
    entries = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=root)
    result = {}
    for row in entries.split(b"\0"):
        if not row:
            continue
        header, raw_name = row.split(b"\t", 1)
        name = raw_name.decode()
        if name not in missing:
            continue
        mode, blob, stage = header.decode().split()
        if stage != "0" or mode not in {"100644", "100755"}:
            raise RuntimeError("Sparse archive is not one regular index blob: " + name)
        result[name] = {"mode": mode, "gitBlob": blob}
    if set(result) != missing:
        raise RuntimeError("Sparse archive index changed while enumerating")
    return dict(sorted(result.items()))


def freeze(root, work):
    names = source_files(root)
    archives = sparse_archives(root)
    receipt = {}
    for name in names:
        if name in archives:
            continue
        source = root / name
        if not source.is_file() or source.is_symlink():
            raise RuntimeError("Frozen evidence requires ordinary source files: " + name)
        content = source.read_bytes()
        target = work / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        shutil.copymode(source, target)
        receipt[name] = {"bytes": len(content), "sha256": sha(content)}
    if (source_files(root) != names or sparse_archives(root) != archives or
            any(sha((root / name).read_bytes()) != row["sha256"] for name, row in receipt.items())):
        raise RuntimeError("Source changed during freeze; no browser was started")
    return receipt, archives


def variants(root):
    rows = []
    for ident, filename, before, after, assertion in CASES:
        source = (root / filename).read_bytes()
        ending = b"\r\n" if b"\r\n" in source else b"\n"
        old, new = (value.encode().replace(b"\n", ending) for value in (before, after))
        if source.count(old) != 1:
            raise RuntimeError(ident + ": mutation anchor must occur exactly once")
        changed = source.replace(old, new, 1)
        rows.append({"id": ident, "file": filename, "assertion": assertion,
                     "before": source, "after": changed,
                     "before_sha256": sha(source), "after_sha256": sha(changed)})
    return rows


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as bound:
        bound.bind(("127.0.0.1", 0))
        return bound.getsockname()[1]


def get_runtime(port):
    with urlopen(f"http://127.0.0.1:{port}/runtime", timeout=2) as response:
        return json.load(response)


def stop(child):
    if child is None or child.poll() is not None:
        return
    if os.name != "nt":
        os.killpg(child.pid, signal.SIGTERM)
    else:
        child.terminate()
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            os.killpg(child.pid, signal.SIGKILL)
        else:
            child.kill()
        child.wait()


def classify(run, assertion=None):
    report = run.get("result") or {}
    if run.get("timedOut") or run.get("error") or not run.get("runtimeUnchanged"):
        return "blocked"
    if report.get("exceptions") != [] or report.get("consoleErrors") != []:
        return "blocked"
    scope = report.get("scope", {})
    if (scope.get("mode") != "partial" or scope.get("included") != ["profile-space"] or
            scope.get("filters") != ["GEOMETRY_SPACE_PROFILE_ONLY"]):
        return "blocked"
    if set(report.get("groups", {})) != {"setup", "profile-space", "browser-health"}:
        return "blocked"
    if report["groups"]["setup"] != {"expected": 2, "passed": 2, "failed": 0, "completed": True}:
        return "blocked"
    group = report.get("groups", {}).get("profile-space", {})
    if group.get("expected") != EXPECTED:
        return "blocked"
    if (run.get("exitCode") == 0 and report.get("completed") is True and report.get("passed") == EXPECTED + 4
            and report.get("failed") == 0 and group == {
                "expected": EXPECTED, "passed": EXPECTED, "failed": 0, "completed": True}
            and report["groups"]["browser-health"] == {"expected": 2, "passed": 2, "failed": 0, "completed": True}):
        return "green"
    failed = [row["name"] for row in report.get("results", [])
              if row.get("ok") is False and row.get("name") not in GENERIC_FAILURES]
    if (assertion and run.get("exitCode") == 1 and failed == [assertion]
            and group.get("failed") == 1 and group.get("passed", 0) > 0):
        return "killed"
    return "blocked" if run.get("exitCode") != 0 else "survived"


def execute(work, out, label, binaries, chrome):
    directory = out / label
    directory.mkdir()
    artifacts = directory / "browser"
    artifacts.mkdir()
    resources = Path(tempfile.mkdtemp(prefix="r12-browser-resources-"))
    port, cdp = free_port(), free_port()
    env = {key: value for key, value in os.environ.items()
           if not (key.startswith("GEOMETRY_") and (key.endswith("_ONLY") or key.startswith("GEOMETRY_CDP_")))}
    env.update(GEOMETRY_BRIDGE_EXECUTABLE=str(binaries["bridge"]),
               GEOMETRY_MODEL_BASE=str(binaries["model-base"]),
               GEOMETRY_FEEDBACK_DIR=str(resources / "feedback"),
               GEOMETRY_TEST_URL=f"http://127.0.0.1:{port}/", GEOMETRY_CDP_PORT=str(cdp),
               GEOMETRY_SPACE_PROFILE_ONLY="1", GEOMETRY_SPACE_TEST_DIR=str(artifacts),
               GEOMETRY_CHROME_PROFILE=str(resources / "chrome-profile"), GEOMETRY_CHROME=chrome)
    command = [os.environ.get("NODE", "node"), "geometry-web/space_model_test.js"]
    report = {"schema": "r12-browser-run/1", "label": label, "startedAt": utc(),
              "cwd": str(work), "command": command, "timeoutSeconds": TIMEOUT,
              "chrome": chrome, "sandboxFlagsAdded": [], "url": env["GEOMETRY_TEST_URL"],
              "binaryHashes": {name: sha(file.read_bytes()) for name, file in binaries.items()},
              "exitCode": None, "timedOut": False, "runtimeUnchanged": False}
    service = child = None
    began = time.monotonic()
    try:
        with (directory / "service.log").open("wb") as service_log:
            service = subprocess.Popen([sys.executable, "geometry-web/serve.py", str(port)],
                                       cwd=work, env=env, stdout=service_log, stderr=subprocess.STDOUT,
                                       start_new_session=os.name != "nt")
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if service.poll() is not None:
                    raise RuntimeError("Isolated service exited before /runtime")
                try:
                    before = get_runtime(port)
                    break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError("Isolated /runtime readiness deadline exceeded")
            if before.get("fresh") is not True or Path(before.get("root", "")).resolve() != work:
                raise RuntimeError("Runtime does not identify this frozen source")
            report["runtimeBefore"] = before
            with (directory / "stdout.log").open("wb") as stdout, (directory / "stderr.log").open("wb") as stderr:
                child = subprocess.Popen(command, cwd=work, env=env, stdout=stdout, stderr=stderr,
                                         start_new_session=os.name != "nt")
                try:
                    report["exitCode"] = child.wait(timeout=TIMEOUT)
                except subprocess.TimeoutExpired:
                    report["timedOut"] = True
                    stop(child)
                    report["exitCode"] = child.returncode
            result_file = artifacts / "result.json"
            if result_file.is_file():
                report["result"] = json.loads(result_file.read_text(encoding="utf-8"))
            after = get_runtime(port)
            report["runtimeAfter"] = after
            report["runtimeUnchanged"] = (after.get("fresh") is True and
                                           after.get("version") == before.get("version") and
                                           after.get("root") == before.get("root"))
    except BaseException as error:
        report["error"] = type(error).__name__ + ": " + str(error)
    finally:
        stop(child)
        stop(service)
        shutil.rmtree(resources)
        report.update(endedAt=utc(), elapsedSeconds=time.monotonic() - began)
        report["logs"] = {p.name: {"bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
                          for p in directory.glob("*.log")}
        write_json(directory / "receipt.json", report)
    print(json.dumps({"run": label, "exitCode": report["exitCode"], "classification": classify(report),
                      "receipt": str(directory / "receipt.json")}), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--withdrawals", action="store_true")
    args = parser.parse_args()
    selected = variants(ROOT)
    anchors = [{key: row[key] for key in ("id", "file", "assertion", "before_sha256", "after_sha256")} for row in selected]
    if args.preflight:
        print(json.dumps({"schema": "r12-browser-withdrawal-anchors/1", "cases": anchors}, ensure_ascii=False, indent=2))
        return 0
    if args.out is None or not args.out.is_absolute():
        parser.error("--out must be a new absolute directory outside the source repository")
    out = args.out.resolve()
    if out == ROOT or ROOT in out.parents or out.exists():
        parser.error("Use a new evidence directory outside the repository")
    chrome = os.environ.get("GEOMETRY_CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome or not Path(chrome).is_file():
        parser.error("GEOMETRY_CHROME must identify an installed browser")
    out.mkdir(parents=True)
    summary = {"schema": "r12-browser-withdrawals/1", "startedAt": utc(), "status": "blocked",
               "sourceCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               "officialMutationLedgerWritten": False, "goldenWritten": False, "anchors": anchors,
               "cases": [], "withdrawalsRequested": args.withdrawals}
    try:
        with tempfile.TemporaryDirectory(prefix="r12-browser-source-") as temporary:
            work = Path(temporary) / "repo"
            work.mkdir()
            sources, archives = freeze(ROOT, work)
            write_json(out / "source-files.json", sources)
            summary["sourceManifestSha256"] = sha((out / "source-files.json").read_bytes())
            write_json(out / "sparse-archives.json", archives)
            summary["sparseArchives"] = {"count": len(archives),
                                          "manifestSha256": sha((out / "sparse-archives.json").read_bytes()),
                                          "prefixes": list(SPARSE_ARCHIVE_PREFIXES),
                                          "scope": "Absent skip-worktree historical receipts only; not runtime/native/browser source."}
            spec = importlib.util.spec_from_file_location("r12_browser_binaries", work / "tests/binaries.py")
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            module.OUT_DIR = Path(temporary) / "binaries"
            with (out / "native-build.log").open("w", encoding="utf-8") as output:
                result = module.build(["bridge", "model-base"], log=lambda line: output.write(str(line) + "\n"))
            if not all(row.ok for row in result.values()):
                raise RuntimeError("Fresh native build blocked: " + str({name: row.status for name, row in result.items()}))
            binaries = {name: module.BY_NAME[name].path for name in ("bridge", "model-base")}
            baseline = execute(work, out, "baseline", binaries, chrome)
            summary["baseline"] = {"exitCode": baseline["exitCode"], "status": classify(baseline)}
            if classify(baseline) != "green":
                raise RuntimeError("Real browser baseline did not complete; no withdrawal was run")
            if args.withdrawals:
                for row in selected:
                    target = work / row["file"]
                    if target.read_bytes() != row["before"]:
                        raise RuntimeError("Frozen target differs from preflight: " + row["id"])
                    target.write_bytes(row["after"])
                    try:
                        mutant = execute(work, out, row["id"], binaries, chrome)
                    finally:
                        if target.read_bytes() != row["after"]:
                            raise RuntimeError("Frozen mutant changed concurrently: " + row["id"])
                        target.write_bytes(row["before"])
                    restored = execute(work, out, row["id"] + "-restored", binaries, chrome)
                    verdict, recovery = classify(mutant, row["assertion"]), classify(restored)
                    summary["cases"].append({"id": row["id"], "namedAssertion": row["assertion"],
                                             "status": verdict, "restored": recovery,
                                             "exitCodes": [baseline["exitCode"], mutant["exitCode"], restored["exitCode"]]})
                    write_json(out / "summary.json", summary)
                    if verdict != "killed" or recovery != "green":
                        raise RuntimeError("Withdrawal or restoration did not meet its named verdict: " + row["id"])
            if any(sha((work / name).read_bytes()) != row["sha256"] for name, row in sources.items()):
                raise RuntimeError("Frozen source was not exactly restored")
            summary["status"] = "passed"
    except BaseException as error:
        summary["error"] = type(error).__name__ + ": " + str(error)
    finally:
        summary["endedAt"] = utc()
        write_json(out / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "error": summary.get("error"), "summary": str(out / "summary.json")}), flush=True)
    return 0 if summary["status"] == "passed" else 2


if __name__ == "__main__":
    sys.exit(main())
