"""Capture two complete Canvas partitions; emit candidates, never acceptance."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
IDS = ("1/2", "2/2")
HELPER = "geometry-web/canvas_capture.js"
FILES = ("plan.json", "source.json", "stdout.log", "stderr.log", "runtime.stdout", "runtime.stderr")
COMMAND = ["node", "geometry-web/cdp_test.js"]
MAX_SECONDS = 35 * 60
GENERATOR_BYTES = 30532
GENERATOR_SHA = "12c161dce158cdb9d8c360a56090beb3cfd8ebaf4a846e47c6e9c9cebd3b01cd"
# The published generator stays immutable. These fixed substitutions rebase
# its frozen inputs onto f9f430f1 / main #402 (P90 8 -> 11), retaining every judge.
# Never learn a new baseline from the checkout or from a failed capture.
REBASED_GENERATOR_BYTES = 30590
REBASED_GENERATOR_SHA = "2f070942be7fd6da66dbcdc42e7b671870d619044ebe121ab611c706df0cb67b"
GENERATOR_REBASE = (
    (b"BASE = '1d304b10ee4451f0557c9b96b28cf31d3f5bde80'",
     b"BASE = 'f9f430f1c14b1f59bad49610758f99a3c4654aa2'", 1),
    (b"GOLDEN: (1483, 'bca2a8425974094e0ab188a5d0c8ba180b05d2d662c90946db5d997515bfcc1b')",
     b"GOLDEN: (1484, '47731559a71bc01ddb608f114707cda3c664b9d8742e37bd5061d464a028b6ef')", 1),
    (b"TEST: (47302, 'ed53e4c69d0fd740e8b310b6bbca8035bde05bccf826de9dd08b759744997ec9')",
     b"TEST: (47521, '7db9dc879d60a4ea52866fb244c51edf735c54aef05d39090bd36911e5e472c6')", 1),
    (b"T_TEST_SHA = 'a04f83bbfbd25c354c9753db9da9d43b27444cdd5a4f5c37d99992577a5b30f9'",
     b"T_TEST_SHA = '2fe8b3e732dedaee07862581c35c1aace69ebf32085e8d91b8cdb1f91921e3b8'", 1),
    (b'4820',
     b'4823', 10),
    (b'4832',
     b'4835', 1),
    (b'const golden=pfExtension.projectGolden(context.golden);',
     b'const golden=r400Extension.projectGolden(pfExtension.projectGolden(context.golden));', 1),
    (b'const golden=pfExtension.projectGolden(beforeWorkspace);',
     b'const golden=r400Extension.projectGolden(pfExtension.projectGolden(beforeWorkspace));', 1),
)
T_BYTES = 1773
T_SHA = "72182fc5a746bbb99b460c5e814e37d79b2d2bde744e33ccb75b9001af985027"
PATCH_NAMES = ("PR396-canvas-complete.patch", "PR396-canvas-T.patch", "PR396-canvas-P.patch")
SCREENSHOT_ENV = {"GEOMETRY_GRID_SYSTEM_SCREENSHOT_DIR": "/tmp/geometry-grid-screens",
                  "GEOMETRY_DOCUMENT_SCREENSHOT_DIR": "/tmp/geometry-document-screens"}


def require(ok, code):
    if not ok:
        raise ValueError(code)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def json_read(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "CAPTURE_DUPLICATE_JSON_KEY:" + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def existing():
    return load_module("pr396_existing_canvas_evidence", ROOT / ".github/scripts/canvas_evidence.py")


def source_identity():
    evidence = existing()
    return {**evidence.source_identity(), **evidence.run_id()}


def source_closure():
    runtime = load_module("pr396_capture_runtime", ROOT / "geometry-web/runtime_version.py")
    files = {path.relative_to(ROOT).as_posix(): sha(path) for path in runtime.source_files(ROOT)}
    return {"version": runtime.source_version(ROOT), "files": files}


def node(payload=None, mode="plan"):
    process = subprocess.run(["node", HELPER, mode], cwd=ROOT,
                             input=None if payload is None else json.dumps(payload).encode(), capture_output=True)
    require(process.returncode == 0, "CAPTURE_TRACE_REJECTED:" + process.stderr.decode("utf-8", errors="replace"))
    result = json_read(process.stdout)
    require(result.get("acceptance") is False, "CAPTURE_MUST_NOT_BE_ACCEPTANCE")
    return result


def plan():
    value = node()
    require(value.get("schema") == "geometry-canvas-capture-plan/1" and value.get("shards") == list(IDS),
            "CAPTURE_PLAN_CHANGED")
    return value


def trace(raw, shard):
    prefixes = {"CDP_SCOPE ": "scopes", "CDP_RESULT ": "results", "CANVAS_SHARD_EVENT ": "events",
                "R11_WORKSPACE_CASE ": "cases", "R11_WORKSPACE_RESULT ": "summaries"}
    found = {name: [] for name in prefixes.values()}
    for line in raw.decode("utf-8", errors="strict").splitlines():
        for prefix, name in prefixes.items():
            if line.startswith(prefix):
                found[name].append(json_read(line[len(prefix):]))
                break
    require(len(found["scopes"]) == 1 and len(found["results"]) == 1, "CAPTURE_ONE_SCOPE_AND_RESULT")
    return {"id": shard, "scope": found["scopes"][0], "result": found["results"][0],
            **{key: found[key] for key in ("events", "cases", "summaries")}}


def runtime_endpoint(environment):
    return existing().runtime_endpoint(environment.get("GEOMETRY_TEST_URL", ""))


def browser_environment(environment):
    require(environment.get("GEOMETRY_CHROME") == "/usr/bin/google-chrome"
            and environment.get("GEOMETRY_CHROME_FLAGS") == "--no-sandbox", "CAPTURE_BROWSER_CONFIG_CHANGED")
    for name, value in SCREENSHOT_ENV.items():
        require(environment.get(name) == value, "CAPTURE_SCREENSHOT_CONFIG_CHANGED:" + name)


def new_output(out):
    require(out != ROOT and ROOT not in out.parents, "CAPTURE_OUTPUT_MUST_BE_EXTERNAL")
    out.mkdir(parents=True, exist_ok=False)


def capture(command, env, stdout, stderr, timeout):
    require(timeout > 0, "CAPTURE_35_MINUTE_LIMIT")
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True)
    errors = []
    def stop(sig):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass
    def copy(stream, path, console):
        try:
            with path.open("wb") as output:
                while chunk := stream.read(65536):
                    output.write(chunk)
                    output.flush()
                    console.buffer.write(chunk)
                    console.buffer.flush()
        except Exception as error:
            errors.append(str(error))
            stop(signal.SIGTERM)
    threads = [threading.Thread(target=copy, args=(process.stdout, stdout, sys.stdout), daemon=True),
               threading.Thread(target=copy, args=(process.stderr, stderr, sys.stderr), daemon=True)]
    for thread in threads:
        thread.start()
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        stop(signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            stop(signal.SIGKILL)
            process.wait()
        raise ValueError("CAPTURE_35_MINUTE_LIMIT")
    finally:
        # Own process group only. A dead driver must not leave a Chrome child
        # holding a log pipe open or continue beyond the original process cap.
        stop(signal.SIGTERM)
        for thread in threads:
            thread.join(timeout=5)
        if any(thread.is_alive() for thread in threads):
            stop(signal.SIGKILL)
            for thread in threads:
                thread.join(timeout=5)
        if not any(thread.is_alive() for thread in threads):
            process.stdout.close()
            process.stderr.close()
        require(not errors and not any(thread.is_alive() for thread in threads), "CAPTURE_LOG_INCOMPLETE:" + str(errors))


def runtime_matches(runtime, receipt, closure):
    require(runtime.get("schema") == "geometry-runtime/1" and runtime.get("fresh") is True,
            "CAPTURE_RUNTIME_NOT_FRESH")
    require(isinstance(receipt.get("execution_root"), str) and runtime.get("root") == receipt["execution_root"]
            and runtime.get("version") == receipt.get("runtime_version") == closure["version"],
            "CAPTURE_RUNTIME_SOURCE_CHANGED")


def scope_matches(payload, receipt):
    scope = payload["scope"]
    environment = receipt["environment"]
    require(scope.get("url") == environment.get("GEOMETRY_TEST_URL")
            and scope.get("feedbackDirectory") == environment.get("GEOMETRY_FEEDBACK_DIR"),
            "CAPTURE_RUNTIME_SCOPE_CHANGED")
    require(scope.get("mode") == "capture-shard" and scope.get("acceptance") is False,
            "CAPTURE_SCOPE_CHANGED")
    require(payload["result"].get("schema") == "geometry-cdp-result/1", "CAPTURE_RESULT_SCHEMA")
    elapsed = payload["result"].get("elapsedSeconds")
    require(type(elapsed) is int and 0 <= elapsed < MAX_SECONDS, "CAPTURE_35_MINUTE_LIMIT")


def capture_environment(shard):
    for key in os.environ:
        if key.startswith("GEOMETRY_") and (key.endswith(("_ONLY", "_CASES", "_CASE"))
                or key == "GEOMETRY_CDP_UPDATE_GOLDEN"):
            raise ValueError("CAPTURE_INHERITED_SCOPE:" + key)
    require(os.environ.get("GEOMETRY_CDP_SHARD", shard) == shard, "CAPTURE_INHERITED_SHARD")
    require(os.environ.get("GEOMETRY_CDP_CAPTURE_P1161", "1") == "1", "CAPTURE_INHERITED_MODE")
    allowed = ("GEOMETRY_TEST_URL", "GEOMETRY_FEEDBACK_DIR", "GEOMETRY_CHROME", "GEOMETRY_CHROME_FLAGS", "GEOMETRY_CDP_PORT", *SCREENSHOT_ENV)
    env = {key: value for key, value in os.environ.items() if not key.startswith("GEOMETRY_")}
    env.update({key: os.environ[key] for key in allowed if key in os.environ})
    env.update(GEOMETRY_CDP_SHARD=shard, GEOMETRY_CDP_CAPTURE_P1161="1", PYTHONDONTWRITEBYTECODE="1")
    browser_environment(env)
    return env


def run(shard, out):
    require(sys.platform.startswith("linux") and shard in IDS, "CAPTURE_LINUX_SHARD_REQUIRED")
    identity, closure, original_plan = source_identity(), source_closure(), plan()
    new_output(out)
    save(out / "plan.json", original_plan)
    save(out / "source.json", closure)
    env = capture_environment(shard)
    port = runtime_endpoint(env)
    env["GEOMETRY_FEEDBACK_DIR"] = str(Path(env["GEOMETRY_FEEDBACK_DIR"]).resolve())
    runtime_command = [sys.executable, "-B", "geometry-web/runtime_version.py", "--probe", str(port)]
    receipt = {"schema": "geometry-canvas-capture-shard/1", "acceptance": False, "capture_verified": False,
               **identity, "shard": shard, "command": COMMAND,
               "runtime_command": ["<python>", *runtime_command[1:]], "plan_sha256": original_plan["sha256"],
               "execution_root": str(ROOT), "runtime_version": closure["version"],
               "environment": {key: env.get(key) for key in ("GEOMETRY_TEST_URL", "GEOMETRY_FEEDBACK_DIR",
                   "GEOMETRY_CHROME", "GEOMETRY_CHROME_FLAGS", "GEOMETRY_CDP_PORT", "GEOMETRY_CDP_SHARD",
                   "GEOMETRY_CDP_CAPTURE_P1161", *SCREENSHOT_ENV)}}
    save(out / "manifest.json", receipt)
    begin = time.monotonic()
    try:
        receipt["runtime_exit"] = capture(runtime_command, env, out / "runtime.stdout", out / "runtime.stderr",
                                          MAX_SECONDS - (time.monotonic() - begin))
        require(receipt["runtime_exit"] == 0, "CAPTURE_RUNTIME_PROBE_FAILED")
        runtime_matches(json_read((out / "runtime.stdout").read_bytes()), receipt, closure)
        receipt["process_exit"] = capture(COMMAND, env, out / "stdout.log", out / "stderr.log",
                                         MAX_SECONDS - (time.monotonic() - begin))
        require(receipt["process_exit"] == 0, "CAPTURE_PROCESS_FAILED")
        payload = trace((out / "stdout.log").read_bytes(), shard)
        scope_matches(payload, receipt)
        verdict = node(payload, "verify-shard")
        require(source_identity() == identity and source_closure() == closure and plan() == original_plan,
                "CAPTURE_SOURCE_CHANGED")
        receipt.update(capture_verified=True, scope=payload["scope"], sections=verdict["sections"],
                       assertions=verdict["assertions"])
    except Exception as error:
        receipt["error"] = str(error)
        raise
    finally:
        receipt["files"] = {name: sha(out / name) for name in FILES if (out / name).is_file()}
        save(out / "manifest.json", receipt)


def verify_manifest(receipt, expected, closure, original_plan, folder):
    require(receipt.get("schema") == "geometry-canvas-capture-shard/1" and receipt.get("acceptance") is False,
            "CAPTURE_RECEIPT_SCHEMA")
    for field in ("execution_sha", "head_sha", "tree", "run_id", "run_attempt"):
        require(receipt.get(field) == expected[field], "CAPTURE_IDENTITY_CHANGED:" + field)
    shard = receipt.get("shard")
    require(shard in IDS and folder.name == "pr396-capture-" + shard[0], "CAPTURE_SHARD_DIRECTORY")
    require(receipt.get("capture_verified") is True and type(receipt.get("process_exit")) is int
            and receipt["process_exit"] == 0 and type(receipt.get("runtime_exit")) is int
            and receipt["runtime_exit"] == 0, "CAPTURE_PROCESS_FAILED")
    require(receipt.get("command") == COMMAND, "CAPTURE_COMMAND_CHANGED")
    environment = receipt.get("environment", {})
    port = runtime_endpoint(environment)
    browser_environment(environment)
    require(environment.get("GEOMETRY_CDP_SHARD") == shard and environment.get("GEOMETRY_CDP_CAPTURE_P1161") == "1",
            "CAPTURE_SCOPE_CHANGED")
    require(receipt.get("runtime_command") == ["<python>", "-B", "geometry-web/runtime_version.py", "--probe", str(port)],
            "CAPTURE_RUNTIME_COMMAND_CHANGED")
    require(receipt.get("plan_sha256") == original_plan["sha256"], "CAPTURE_PLAN_CHANGED")
    require(set(receipt.get("files", {})) == set(FILES), "CAPTURE_MISSING_RAW")
    for name in FILES:
        path = folder / name
        require(path.is_file() and not path.is_symlink() and sha(path) == receipt["files"][name],
                "CAPTURE_RAW_CHANGED:" + name)
    require(json_read((folder / "plan.json").read_bytes()) == original_plan, "CAPTURE_PLAN_CHANGED")
    require(json_read((folder / "source.json").read_bytes()) == closure, "CAPTURE_SOURCE_CHANGED")
    runtime_matches(json_read((folder / "runtime.stdout").read_bytes()), receipt, closure)
    payload = trace((folder / "stdout.log").read_bytes(), shard)
    scope_matches(payload, receipt)
    require(receipt.get("scope") == payload["scope"] and receipt.get("sections") == payload["result"].get("sections")
            and receipt.get("assertions") == payload["result"].get("passedAssertions"), "CAPTURE_FAKE_SUMMARY")
    return payload


def rebase_generator(raw):
    for old, new, count in GENERATOR_REBASE:
        require(raw.count(old) == count, "CAPTURE_GENERATOR_REBASE_ANCHOR")
        raw = raw.replace(old, new)
    require(len(raw) == REBASED_GENERATOR_BYTES and hashlib.sha256(raw).hexdigest() == REBASED_GENERATOR_SHA,
            "CAPTURE_GENERATOR_REBASE_CHANGED")
    return raw


def generator(path):
    raw = path.read_bytes()
    require(len(raw) == GENERATOR_BYTES and hashlib.sha256(raw).hexdigest() == GENERATOR_SHA,
            "CAPTURE_GENERATOR_CHANGED")
    t_path = path.with_name("PR396-canvas-T.patch")
    t_raw = t_path.read_bytes()
    require(len(t_raw) == T_BYTES and hashlib.sha256(t_raw).hexdigest() == T_SHA, "CAPTURE_T_CHANGED")
    # Both published files are verified before the fixed, separately pinned rebase.
    raw = rebase_generator(raw)
    # Execute these exact verified bytes, not a second read of the path.
    module = ModuleType("pr396_original_generator")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module, t_path, t_raw


def candidate_sources(tool, before, t_test, count):
    after = tool.render_after(before, t_test, count)
    old = b"// Its exact count was captured from one full, zero-failure cdp_test.js run.\n"
    new = (b"// Its exact count was observed in two complete capture partitions using the existing handoff.\n"
           b"// This is a candidate count; final-head strict Canvas replay remains required.\n")
    require(after[tool.TEST].count(old) == 1, "CAPTURE_PROVENANCE_ANCHOR")
    after[tool.TEST] = after[tool.TEST].replace(old, new, 1)
    return after


def candidates(before, count, tool, t_path, t_raw, out, execution):
    with tempfile.TemporaryDirectory(prefix="pr396-capture-judge-") as directory:
        temporary = Path(directory)
        root = temporary / "checkout"
        root.mkdir()
        # Stream the archive: the source repository may be several GiB.
        # Keeping both source.tar and the extracted tree needlessly doubles it.
        archive_process = subprocess.Popen(["git", "archive", "--format=tar", execution], cwd=ROOT,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            with tarfile.open(fileobj=archive_process.stdout, mode="r|") as archive:
                archive.extractall(root, filter="data")
            errors = archive_process.stderr.read()
            require(archive_process.wait() == 0, "CAPTURE_ARCHIVE_FAILED:" + errors.decode("utf-8", errors="replace"))
        finally:
            if archive_process.poll() is None:
                archive_process.kill()
                archive_process.wait()
            archive_process.stdout.close()
            archive_process.stderr.close()
        require(tool.before_files(root) == before, "CAPTURE_ARCHIVE_BEFORE_CHANGED")
        t_path = temporary / "verified-T.patch"
        t_path.write_bytes(t_raw)
        subprocess.run(["git", "apply", "--check", str(t_path)], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "apply", str(t_path)], cwd=root, check=True, capture_output=True)
        t_test = (root / tool.TEST).read_bytes()
        after = candidate_sources(tool, before, t_test, count)
        env = {key: value for key, value in os.environ.items() if not key.startswith("GEOMETRY_")}
        mutants = tool.normal_checks(root, out, env, before, t_test, after)
        intermediate = dict(before)
        intermediate[tool.TEST] = t_test
        payloads = {PATCH_NAMES[0]: tool.make_patch(before, after), PATCH_NAMES[1]: t_raw,
                    PATCH_NAMES[2]: tool.make_patch(intermediate, after)}
        proof = tool.verify_patch_paths(before, intermediate, after, payloads)
        return payloads, {"mutants": mutants, "patch_apply_verification": proof,
            "files": [{"path": name, "before": tool.metadata(before[name]),
                       "after_T": tool.metadata(intermediate[name]), "after": tool.metadata(after[name])}
                      for name in tool.FILES], "patches": {name: tool.metadata(raw) for name, raw in payloads.items()}}


def verify(artifacts, out, generator_path):
    expected, closure, original_plan = source_identity(), source_closure(), plan()
    tool, t_path, t_raw = generator(generator_path)
    before = tool.before_files(ROOT)
    new_output(out)
    status = {"schema": "geometry-canvas-capture-candidate-status/1", "acceptance": False,
              "capture_verified": False, "patches_written": False, **expected}
    save(out / "status.json", status)
    try:
        folders = sorted(artifacts.iterdir())
        require(len(folders) == 2 and all(folder.is_dir() and not folder.is_symlink()
                and (folder / "manifest.json").is_file() and not (folder / "manifest.json").is_symlink()
                for folder in folders), "CAPTURE_TWO_RAW_SHARDS_REQUIRED")
        payloads, manifests, seen = [], [], set()
        for folder in folders:
            receipt = json_read((folder / "manifest.json").read_bytes())
            require(receipt.get("shard") not in seen, "CAPTURE_DUPLICATE_SHARD")
            seen.add(receipt.get("shard"))
            payloads.append(verify_manifest(receipt, expected, closure, original_plan, folder))
            manifests.append(receipt)
        require(seen == set(IDS), "CAPTURE_TWO_RAW_SHARDS_REQUIRED")
        verdict = node({"receipts": payloads}, "verify")
        require(verdict.get("passed") is True and type(verdict.get("P1161")) is int and verdict["P1161"] > 0,
                "CAPTURE_EXACT_COUNT_REQUIRED")
        require(source_identity() == expected and source_closure() == closure and plan() == original_plan,
                "CAPTURE_SOURCE_CHANGED")
        patch_payloads, proof = candidates(before, verdict["P1161"], tool, t_path, t_raw, out, expected["execution_sha"])
        require(source_identity() == expected and source_closure() == closure and plan() == original_plan,
                "CAPTURE_SOURCE_CHANGED")
        manifest = {"schema": "geometry-canvas-capture-candidate/1", "acceptance": False,
                    "basis": "two complete contiguous capture partitions with the existing handoff; not a full browser process",
                    **expected, "plan_sha256": original_plan["sha256"], "source": closure,
                    "P1161": verdict["P1161"], "capture": verdict, "shards": manifests,
                    "generator": {"bytes": GENERATOR_BYTES, "sha256": GENERATOR_SHA,
                                  "rebased": {"bytes": REBASED_GENERATOR_BYTES, "sha256": REBASED_GENERATOR_SHA,
                                              "baseline_head": "f9f430f1c14b1f59bad49610758f99a3c4654aa2"}}, **proof,
                    "generation_note": "The exact published generator and T are verified first; fixed, hash-pinned substitutions refresh only baseline inputs and P90 projection anchors. All original judges remain. The new helper comment identifies two capture partitions instead of one full process.",
                    "limits": ["Candidate counts only; final-head strict Canvas 1/2, 2/2 and complete coverage remain required."]}
        save(out / "manifest.json", manifest)
        for name, raw in patch_payloads.items():
            (out / name).write_bytes(raw)
        status.update(capture_verified=True, patches_written=True, P1161=verdict["P1161"])
        save(out / "status.json", status)
        print(json.dumps(status))
    except Exception as error:
        for name in (*PATCH_NAMES, "manifest.json"):
            (out / name).unlink(missing_ok=True)
        status["error"] = str(error)
        save(out / "status.json", status)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify", "generator-self-test"))
    parser.add_argument("--shard", choices=IDS)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--repo", type=Path, default=ROOT)
    args = parser.parse_args()
    ROOT = args.repo.resolve()
    if args.mode == "generator-self-test":
        parser.error("generator-self-test requires --generator") if args.generator is None else None
        tool, _, _ = generator(args.generator.resolve())
        raise SystemExit(tool.self_test(ROOT))
    parser.error("run/verify requires --out") if args.out is None else None
    if args.mode == "run":
        parser.error("run requires --shard") if args.shard is None else None
        run(args.shard, args.out.resolve())
    else:
        parser.error("verify requires --input and --generator") if args.input is None or args.generator is None else None
        verify(args.input.resolve(), args.out.resolve(), args.generator.resolve())
