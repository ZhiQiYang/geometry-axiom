#!/usr/bin/env python3
"""Record one isolated command against a clean, source-pinned Geometry runtime.

Usage: python tests/release_gate.py --url http://127.0.0.1:18970/ \
         --output /tmp/new-evidence-directory -- node geometry-web/cdp_test.js

Requires GEOMETRY_TEST_BRIDGE and GEOMETRY_MODEL_BASE with registry receipts.
This verifies execution of the named command, never a complete product release.
An arbitrary command's exit 0 is not a test count or proof of test completion.
CDP/Space commands additionally require their canonical structured result.
The caller owns the isolated server. This tool never starts or stops that server.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
from urllib.parse import urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "geometry-release-command/1"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def normalize_url(value):
    parsed = urlsplit(value)
    if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
            or parsed.username or parsed.password or parsed.path not in {"", "/"}
            or parsed.query or parsed.fragment or not parsed.port):
        raise ValueError("--url must be an explicit loopback HTTP service with a port and no path")
    return value.rstrip("/") + "/"


def runtime_status(url):
    with urlopen(url + "runtime", timeout=10) as response:
        if response.status != 200:
            raise ValueError("/runtime did not return HTTP 200")
        data = response.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError("/runtime response exceeds 1 MiB")
    return json.loads(data)


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                            text=True, encoding="utf-8", timeout=20, check=True)
    return result.stdout.strip()


def snapshot(root, url, env):
    """Collect all available diagnostics even when one precondition fails."""
    result = {"at": now(), "root": str(root), "problems": []}
    try:
        actual = Path(git(root, "rev-parse", "--show-toplevel")).resolve()
        result["git"] = {"root": str(actual), "head": git(root, "rev-parse", "HEAD"),
                         "tree": git(root, "rev-parse", "HEAD^{tree}"),
                         "status": git(root, "status", "--porcelain=v1", "--untracked-files=all")}
        if actual != root or result["git"]["status"]:
            result["problems"].append("repository must be the exact clean root (including untracked files)")
    except Exception as error:
        result["problems"].append("git: " + str(error))
    try:
        runtime = module(root / "geometry-web/runtime_version.py", "release_runtime")
        result["sourceVersion"] = runtime.source_version(root)
        result["runtime"] = runtime_status(url)
        observed = result["runtime"]
        if (not isinstance(observed, dict) or observed.get("schema") != "geometry-runtime/1"
                or observed.get("fresh") is not True
                or observed.get("version") != result["sourceVersion"]
                or not isinstance(observed.get("root"), str)
                or Path(observed["root"]).resolve() != root
                or type(observed.get("pid")) is not int or observed["pid"] <= 0
                or not isinstance(observed.get("session"), str) or not observed["session"]):
            result["problems"].append("runtime schema/root/source/fresh/session/pid mismatch")
    except Exception as error:
        result["problems"].append("runtime: " + str(error))
    result["native"] = {}
    try:
        binaries = module(root / "tests/binaries.py", "release_binaries")
        for name, key in (("bridge", "GEOMETRY_TEST_BRIDGE"), ("model-base", "GEOMETRY_MODEL_BASE")):
            value = env.get(key)
            if not value:
                result["problems"].append(key + " must point to a receipt-backed native executable")
                continue
            info = binaries.inspect_one(binaries.BY_NAME[name], path=value)
            entry = result["native"][name] = info.as_dict()
            entry["fingerprint"] = info.fingerprint
            if info.state != "fresh":
                result["problems"].append(name + " native is not fresh: " + info.reason)
                continue
            entry["sha256"] = sha(info.path)
            entry["sidecarSha256"] = sha(info.path.with_name(info.path.name + binaries.SIDECAR_SUFFIX))
        if env.get("GEOMETRY_BRIDGE") and "bridge" in result["native"]:
            if Path(env["GEOMETRY_BRIDGE"]).resolve() != Path(result["native"]["bridge"]["path"]).resolve():
                result["problems"].append("GEOMETRY_BRIDGE differs from the verified GEOMETRY_TEST_BRIDGE executable")
    except Exception as error:
        result["problems"].append("native: " + str(error))
    return result


def compare_snapshots(before, after):
    problems = list(after.get("problems", []))
    for key in ("root", "git", "sourceVersion", "native"):
        if before.get(key) != after.get(key):
            problems.append(key + " changed during execution")
    for key in ("schema", "root", "version", "session", "pid"):
        if before.get("runtime", {}).get(key) != after.get("runtime", {}).get(key):
            problems.append("runtime " + key + " changed during execution")
    return problems


def command_kind(command, root):
    for name, kind in (("cdp_test.js", "cdp"), ("space_model_test.js", "space")):
        target = root / "geometry-web" / name
        if any((root / arg).resolve() == target for arg in command[1:] if not arg.startswith("-")):
            return kind
    return "command"


def inspect_result(log, kind, root, expected_url=None):
    """Only recognize existing canonical result protocols; do not infer pass from prose."""
    if kind == "command":
        return {"scope": "command-only", "completionVerified": False,
                "note": "Exit status recorded; no generic test-completion or release claim."}, []
    prefix = "CDP_RESULT " if kind == "cdp" else "SPACE_RESULT "
    rows = []
    with Path(log).open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if line.startswith(prefix):
                try:
                    rows.append(json.loads(line[len(prefix):]))
                except ValueError:
                    return {"scope": "unknown", "completionVerified": False}, ["malformed canonical result"]
    if len(rows) != 1 or not isinstance(rows[0], dict):
        return {"scope": "unknown", "completionVerified": False}, ["expected exactly one canonical result"]
    row, problems = rows[0], []
    expected_schema = "geometry-cdp-result/1" if kind == "cdp" else "geometry-space-result/1"
    scope = row.get("scope")
    mode = scope.get("mode") if isinstance(scope, dict) else None
    valid_modes = {"full", "partial"} if kind == "cdp" else {"full-space-suite", "partial"}
    if row.get("schema") != expected_schema or row.get("completed") is not True or mode not in valid_modes:
        problems.append("canonical result is incomplete or has an unknown schema/scope")
    if expected_url is not None and (not isinstance(scope, dict) or scope.get("url") != expected_url):
        problems.append("canonical command used a different service URL")
    passed_key, failed_key = ("passedAssertions", "failedAssertions") if kind == "cdp" else ("passed", "failed")
    if type(row.get(passed_key)) is not int or row[passed_key] <= 0 or row.get(failed_key) != 0:
        problems.append("canonical result has failures or no positive assertion census")
    if kind == "cdp":
        if row.get("skipped") != [] or row.get("sectionsFailed"):
            problems.append("CDP contains skips or failed sections")
        if mode == "full":
            golden = json.loads((root / "geometry-web/cdp_sections.golden.json").read_text(encoding="utf-8"))
            if (row.get("goldenCompare") != "matched" or scope.get("filters") != []
                    or scope.get("modifiers") != [] or row.get("sections") != golden["sections"]
                    or row.get("passedAssertions") != golden["total"]):
                problems.append("full CDP did not match the committed complete census")
    else:
        # Ask the committed census helper, not a second hard-coded copy of its floors.
        floors = subprocess.run(["node", "-e", "process.stdout.write(JSON.stringify(require(process.argv[1])))",
                                 str(root / "geometry-web/space_test_floor.js")],
                                capture_output=True, text=True, timeout=10, check=True)
        declared = json.loads(floors.stdout)
        groups = row.get("groups")
        if row.get("exceptions") != [] or row.get("consoleErrors") != [] or row.get("completenessProblems") != []:
            problems.append("Space contains browser errors or completeness problems")
        if not isinstance(groups, dict) or not groups:
            problems.append("Space group census missing")
        else:
            for name, group in groups.items():
                if (not isinstance(group, dict) or group.get("completed") is not True
                        or type(group.get("expected")) is not int
                        or group.get("expected") != declared["EXPECTED"].get(name)
                        or group.get("passed") != group.get("expected") or group.get("failed") != 0):
                    problems.append("Space group census is incomplete")
                    break
            if isinstance(scope, dict) and set(groups) != set(["setup", *scope.get("included", []), "browser-health"]):
                problems.append("Space groups do not match the declared scope")
            if all(isinstance(g, dict) and type(g.get("passed")) is int for g in groups.values()):
                if sum(g["passed"] for g in groups.values()) != row.get("passed"):
                    problems.append("Space total differs from group census")
        if mode == "full-space-suite" and (scope.get("filters") != []
                                           or scope.get("included") != declared["FULL_SPACE_GROUPS"]):
            problems.append("full Space result does not include its complete declared suite")
    return {"scope": scope, "completionVerified": not problems, "canonicalResult": row}, problems


def stop_child(child):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], capture_output=True, timeout=15)
    else:
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    child.wait(timeout=15)


def execute(command, root, env, log, timeout):
    result = {"started": now(), "exitCode": None, "timedOut": False, "interrupted": False}
    child = None
    with Path(log).open("xb") as stream:
        try:
            child = subprocess.Popen(command, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                     start_new_session=os.name != "nt")
            result["pid"] = child.pid
            result["exitCode"] = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            result["timedOut"] = True
        except (KeyboardInterrupt, InterruptedError) as error:
            result["interrupted"] = True
            result["error"] = str(error) or "interrupted"
        except Exception as error:
            result["error"] = str(error)
        finally:
            if child is not None and (result["timedOut"] or result["interrupted"] or child.poll() is None):
                stop_child(child)
            if child is not None:
                result["exitCode"] = child.returncode
    result["finished"] = now()
    return result


def run_gate(root, url, output, command, env, timeout, *, capture=snapshot, runner=execute):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output == root or root in output.parents:
        raise ValueError("--output must be outside the checkout")
    output.mkdir(parents=True, exist_ok=False)
    receipt = {"schema": SCHEMA, "created": now(), "command": command, "cwd": str(root),
               "url": url, "timeoutSeconds": timeout, "platform": platform.platform(),
               "python": sys.version, "status": "rejected", "executionVerified": False,
               "releaseApproved": False, "problems": [],
               "limitations": ["Only this command is covered; independent delivery gates remain separate.",
                               "Native receipts attest configured files; /runtime does not attest the running native process.",
                               "Before/after identity checks do not prove absence of transient source changes."]}
    log = output / "command.log"
    code = 2
    try:
        url = normalize_url(url)
        child_env = dict(env, GEOMETRY_TEST_URL=url, PYTHONDONTWRITEBYTECODE="1")
        receipt["environment"] = {key: value for key, value in child_env.items()
                                  if key in {"GEOMETRY_TEST_URL", "GEOMETRY_FEEDBACK_DIR", "GEOMETRY_TEST_BRIDGE",
                                             "GEOMETRY_MODEL_BASE", "GEOMETRY_BRIDGE", "GEOMETRY_CHROME", "GEOMETRY_CDP_PORT"}
                                  or key.startswith("GEOMETRY_") and (key.endswith("_ONLY") or key == "GEOMETRY_CDP_FROM_P31")}
        if not command:
            raise ValueError("a canonical command after -- is required")
        receipt["kind"] = command_kind(command, root)
        receipt["before"] = capture(root, url, child_env)
        receipt["problems"].extend(receipt["before"]["problems"])
        if not receipt["problems"]:
            receipt["execution"] = runner(command, root, child_env, log, timeout)
            receipt["after"] = capture(root, url, child_env)
            receipt["problems"].extend(compare_snapshots(receipt["before"], receipt["after"]))
            execution = receipt["execution"]
            if execution.get("timedOut"):
                receipt["status"], code = "timed-out", 124
            elif execution.get("interrupted"):
                receipt["status"], code = "interrupted", 130
            elif execution.get("error") or execution.get("exitCode") != 0:
                receipt["status"], code = "command-failed", 1
            else:
                evidence, problems = inspect_result(log, receipt["kind"], root, url)
                receipt["evidence"] = evidence
                receipt["problems"].extend(problems)
                if not receipt["problems"]:
                    receipt["status"], code = "execution-verified", 0
                    receipt["executionVerified"] = True
    except (KeyboardInterrupt, InterruptedError) as error:
        receipt["status"], code = "interrupted", 130
        receipt["problems"].append(str(error) or "interrupted")
    except Exception as error:
        receipt["problems"].append(str(error))
    finally:
        if not log.exists():
            log.touch(exist_ok=False)
        receipt["log"] = {"path": str(log), "bytes": log.stat().st_size, "sha256": sha(log)}
        receipt["finished"], receipt["gateExitCode"] = now(), code
        temporary = output / "receipt.json.tmp"
        temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(output / "receipt.json")
    return code, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=2400)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.output.is_absolute() or not 0 < args.timeout <= 86400:
        parser.error("--output must be absolute; --timeout must be positive and at most 86400 seconds")
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    def interrupted(signum, _frame):
        raise InterruptedError("received signal " + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    try:
        code, receipt = run_gate(ROOT, args.url, args.output, command, os.environ, args.timeout)
    except (OSError, ValueError) as error:
        print("Release command refused: " + str(error), file=sys.stderr)
        return 2
    print(json.dumps({"status": receipt["status"], "executionVerified": receipt["executionVerified"],
                      "releaseApproved": False, "receipt": str(args.output / "receipt.json"),
                      "problems": receipt["problems"]}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
