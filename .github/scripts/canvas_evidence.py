"""Supervise the original CDP assertions and verify their two exact receipts."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
IDS = ("1/2", "2/2")
HELPER = "tests/helpers/canvas_shards.js"
FILES = ("plan.json", "stdout.log", "stderr.log", "runtime.stdout", "runtime.stderr")


def require(ok, code):
    if not ok:
        raise ValueError(code)


def read_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "CANVAS_DUPLICATE_JSON_KEY: " + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def source_identity():
    require(not git("status", "--porcelain=v1"), "CANVAS_DIRTY_SOURCE")
    execution = git("rev-parse", "HEAD")
    expected = os.environ.get("EXPECTED_EXECUTION_SHA", execution)
    require(execution == expected, "CANVAS_WRONG_HEAD")
    head = os.environ.get("PR_HEAD_SHA", execution)
    # Actions checkout is shallow. Pretty/rev-list parent traversal can hide
    # the boundary parents; the immutable commit object still contains them.
    header = git("cat-file", "-p", execution).split("\n\n", 1)[0]
    parents = [line.removeprefix("parent ") for line in header.splitlines() if line.startswith("parent ")]
    require(head == execution or head in parents, "CANVAS_WRONG_PR_HEAD")
    return {"execution_sha": execution, "head_sha": head, "tree": git("rev-parse", "HEAD^{tree}")}


def plan():
    raw = subprocess.check_output(["node", HELPER, "plan"], cwd=ROOT)
    current = read_json(raw)
    require(current.get("shards") == list(IDS), "CANVAS_SHARD_PLAN_CHANGED")
    return current


def trace(raw):
    events, results = [], []
    for line in raw.decode("utf-8", errors="strict").splitlines():
        if line.startswith("CANVAS_SHARD_EVENT "):
            events.append(read_json(line.removeprefix("CANVAS_SHARD_EVENT ")))
        if line.startswith("CDP_RESULT "):
            results.append(read_json(line.removeprefix("CDP_RESULT ")))
    require(len(results) == 1, "CANVAS_RESULT_COUNT")
    return events, results[0]


def node_verify(payload, mode="verify"):
    process = subprocess.run(["node", HELPER, mode], cwd=ROOT,
                             input=json.dumps(payload, ensure_ascii=False).encode(), capture_output=True)
    require(process.returncode == 0, "CANVAS_TRACE_REJECTED: " + process.stderr.decode("utf-8", errors="replace"))
    return read_json(process.stdout)


def run_id():
    value = os.environ.get("GITHUB_RUN_ID")
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT")
    require(value is not None and value.isdigit() and attempt is not None and attempt.isdigit(), "CANVAS_RUN_ID_REQUIRED")
    return {"run_id": value, "run_attempt": attempt}


def runtime_version():
    spec = importlib.util.spec_from_file_location("canvas_runtime_identity", ROOT / "geometry-web/runtime_version.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.source_version(ROOT)


def runtime_endpoint(url):
    endpoint = urlparse(url)
    require(endpoint.scheme == "http" and endpoint.hostname == "127.0.0.1" and endpoint.port is not None
            and endpoint.path == "/" and not endpoint.query and not endpoint.fragment and not endpoint.username and not endpoint.password,
            "CANVAS_RUNTIME_ENDPOINT")
    return endpoint.port


def capture(command, out, err, env):
    """Wait for both real pipes to close before publishing any success receipt."""
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    def copy(stream, target, console):
        with target.open("wb") as output:
            while chunk := stream.read(65536):
                output.write(chunk)
                output.flush()
                console.buffer.write(chunk)
                console.buffer.flush()
    threads = [threading.Thread(target=copy, args=(process.stdout, out, sys.stdout)),
               threading.Thread(target=copy, args=(process.stderr, err, sys.stderr))]
    for thread in threads:
        thread.start()
    status = process.wait()
    for thread in threads:
        thread.join()
    return status


def run(shard, out):
    require(shard in IDS, "CANVAS_FAKE_SCOPE")
    identity, run = source_identity(), run_id()
    out.mkdir(parents=True, exist_ok=False)
    original_plan = plan()
    save(out / "plan.json", original_plan)
    env = dict(os.environ, GEOMETRY_CDP_SHARD=shard, PYTHONDONTWRITEBYTECODE="1")
    port = runtime_endpoint(env["GEOMETRY_TEST_URL"])
    env["GEOMETRY_TEST_URL"] = f"http://127.0.0.1:{port}/"
    env["GEOMETRY_FEEDBACK_DIR"] = str(Path(env["GEOMETRY_FEEDBACK_DIR"]).resolve())
    runtime_command = [sys.executable, "-B", "geometry-web/runtime_version.py", "--probe", str(port)]
    runtime_exit = capture(runtime_command, out / "runtime.stdout", out / "runtime.stderr", env)
    require(runtime_exit == 0, "CANVAS_RUNTIME_PROBE_FAILED")
    runtime = read_json((out / "runtime.stdout").read_bytes())
    require(runtime.get("fresh") is True and runtime.get("schema") == "geometry-runtime/1", "CANVAS_RUNTIME_NOT_FRESH")
    command = ["node", "geometry-web/cdp_test.js"]
    status = capture(command, out / "stdout.log", out / "stderr.log", env)
    receipt = {"schema": "geometry-canvas-shard/1", **identity, **run, "shard": shard,
               "command": command, "runtime_command": ["<python>", *runtime_command[1:]],
               "process_exit": status, "runtime_exit": runtime_exit, "plan_sha256": original_plan["sha256"],
               "execution_root": str(ROOT), "runtime_version": runtime["version"],
               "environment": {name: env.get(name) for name in ("GEOMETRY_TEST_URL", "GEOMETRY_FEEDBACK_DIR", "GEOMETRY_CHROME",
                   "GEOMETRY_CHROME_FLAGS", "GEOMETRY_CDP_PORT", "GEOMETRY_CDP_SHARD")},
               "platform": sys.platform, "python": sys.version, "node": subprocess.check_output(["node", "--version"], text=True).strip(),
               "files": {name: sha(out / name) for name in FILES}, "verified": False}
    save(out / "manifest.json", receipt)
    require(status == 0, "CANVAS_PROCESS_FAILED: " + str(status))
    events, result = trace((out / "stdout.log").read_bytes())
    verified = node_verify({"id": shard, "events": events, "result": result}, "verify-shard")
    require(source_identity() == identity and plan() == original_plan and runtime["version"] == runtime_version(), "CANVAS_SOURCE_CHANGED")
    receipt.update(verified=True, scope=result["scope"], sections=verified["sections"], assertions=verified["assertions"])
    save(out / "manifest.json", receipt)


def verify_manifest(receipt, expected, original_plan, folder):
    require(receipt.get("schema") == "geometry-canvas-shard/1", "CANVAS_RECEIPT_SCHEMA")
    for field in ("execution_sha", "head_sha", "tree"):
        require(receipt.get(field) == expected[field], "CANVAS_WRONG_HEAD: " + field)
    for field in ("run_id", "run_attempt"):
        require(receipt.get(field) == expected[field], "CANVAS_WRONG_RUN_ATTEMPT: " + field)
    require(receipt.get("shard") in IDS, "CANVAS_FAKE_SCOPE")
    require(folder.name == "canvas-shard-" + receipt["shard"].split("/")[0], "CANVAS_RECEIPT_DIRECTORY")
    require(receipt.get("verified") is True and type(receipt.get("process_exit")) is int and receipt["process_exit"] == 0
            and type(receipt.get("runtime_exit")) is int and receipt["runtime_exit"] == 0, "CANVAS_PROCESS_FAILED")
    require(receipt.get("command") == ["node", "geometry-web/cdp_test.js"], "CANVAS_COMMAND_CHANGED")
    environment = receipt.get("environment", {})
    port = runtime_endpoint(environment.get("GEOMETRY_TEST_URL", ""))
    require(environment.get("GEOMETRY_CDP_SHARD") == receipt["shard"], "CANVAS_FAKE_SCOPE")
    require(receipt.get("runtime_command") == ["<python>", "-B", "geometry-web/runtime_version.py", "--probe", str(port)],
            "CANVAS_RUNTIME_COMMAND_CHANGED")
    require(receipt.get("plan_sha256") == original_plan["sha256"], "CANVAS_SOURCE_OR_GOLDEN_CHANGED")
    require(set(receipt.get("files", {})) == set(FILES), "CANVAS_MISSING_RAW")
    for name in FILES:
        require((folder / name).is_file() and sha(folder / name) == receipt["files"][name], "CANVAS_RAW_CHANGED: " + name)
    require(read_json((folder / "plan.json").read_bytes()) == original_plan, "CANVAS_SOURCE_OR_GOLDEN_CHANGED")
    runtime = read_json((folder / "runtime.stdout").read_bytes())
    require(runtime.get("fresh") is True and runtime.get("schema") == "geometry-runtime/1", "CANVAS_RUNTIME_NOT_FRESH")
    require(runtime.get("root") == receipt.get("execution_root") and isinstance(runtime.get("root"), str)
            and runtime.get("version") == expected["runtime_version"] == receipt.get("runtime_version"), "CANVAS_RUNTIME_SOURCE_CHANGED")
    events, result = trace((folder / "stdout.log").read_bytes())
    require(result.get("schema") == "geometry-cdp-result/1", "CANVAS_RESULT_SCHEMA")
    require(result.get("scope", {}).get("url") == environment["GEOMETRY_TEST_URL"]
            and result.get("scope", {}).get("feedbackDirectory") == environment.get("GEOMETRY_FEEDBACK_DIR"), "CANVAS_RUNTIME_SCOPE_CHANGED")
    require(receipt.get("scope") == result.get("scope") and receipt.get("sections") == result.get("sections")
            and receipt.get("assertions") == result.get("passedAssertions"), "CANVAS_FAKE_SUMMARY")
    return {"id": receipt["shard"], "events": events, "result": result}


def verify(artifacts, out):
    expected = {**source_identity(), **run_id(), "runtime_version": runtime_version()}
    original_plan = plan()
    # Preserve #369's strict input set: do not silently ignore an extra folder
    # or a failed shard whose manifest was never completed.
    folders = sorted(artifacts.iterdir())
    require(all(folder.is_dir() and not folder.is_symlink() and (folder / "manifest.json").is_file()
                for folder in folders), "CANVAS_MISSING_RAW")
    require(len(folders) == len(IDS), "CANVAS_MISSING_SHARD")
    shards, manifests, seen = [], [], set()
    for folder in folders:
        receipt = read_json((folder / "manifest.json").read_bytes())
        require(receipt.get("shard") not in seen, "CANVAS_DUPLICATE_SHARD")
        seen.add(receipt.get("shard"))
        shards.append(verify_manifest(receipt, expected, original_plan, folder))
        manifests.append(receipt)
    require(seen == set(IDS), "CANVAS_MISSING_SHARD")
    result = node_verify({"shards": shards})
    require(source_identity() == {key: expected[key] for key in ("execution_sha", "head_sha", "tree")}, "CANVAS_SOURCE_CHANGED")
    out.mkdir(parents=True, exist_ok=False)
    save(out / "summary.json", {"schema": "geometry-canvas-summary/1", **expected, "plan_sha256": original_plan["sha256"],
                               "golden_sha256": original_plan["sourceHashes"]["geometry-web/cdp_sections.golden.json"],
                               "strict_exit": 0, "disjoint_union_equals_current_golden": True, **result, "shards": manifests})
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    parser.add_argument("--shard", choices=IDS)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--artifacts", type=Path)
    args = parser.parse_args()
    if args.mode == "plan":
        print(json.dumps(plan(), ensure_ascii=False))
    elif args.mode == "run":
        run(args.shard, args.out.resolve())
    else:
        verify(args.artifacts.resolve(), args.out.resolve())
