"""Compare the original H15 assertion with and without GEOMETRY_MODEL_BASE."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

target = "d7fd78cebfa9baea47eca39110d1a6f1cf333f79"
root = Path(sys.argv[1]).resolve()
report = Path(sys.argv[2]).resolve()
report.mkdir(parents=True, exist_ok=False)
script = "tests/test_r13_reconstruction_store.js"
native = Path("/tmp/geometry-tests/model-base")
environment = {k: os.environ[k] for k in ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR") if k in os.environ}
environment["PYTHONDONTWRITEBYTECODE"] = "1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=root, env=environment, text=True).strip()


def record(name, command, env, timeout):
    process = subprocess.run(command, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    (report / (name + ".stdout")).write_bytes(process.stdout)
    (report / (name + ".stderr")).write_bytes(process.stderr)
    return process


assert git("rev-parse", "HEAD") == target
assert not git("status", "--porcelain=v1")
assert not native.exists(), "fresh GitHub runner expected"
build = record("build", [sys.executable, "-B", "tests/binaries.py", "build", "model-base"], environment, 300)
assert build.returncode == 0 and native.is_file()
node = Path(shutil.which("node", path=environment["PATH"])).resolve()
node_version = subprocess.check_output([str(node), "--version"], env=environment, text=True).strip()
assert node_version.startswith("v24.")
command = [str(node), "--test", "--test-name-pattern=^R13_H15 ", "--test-reporter=tap", script]
identity = {
    "commit": target, "tree": git("rev-parse", "HEAD^{tree}"),
    "test_git_blob": git("rev-parse", "HEAD:" + script), "test_file_sha256": digest(root / script),
    "node": str(node), "node_version": node_version, "node_sha256": digest(node),
    "binary": str(native), "binary_sha256": digest(native), "command": command,
}
for sidecar in native.parent.glob("model-base*.json"):
    shutil.copyfile(sidecar, report / sidecar.name)
runs = []
for label, model in (("set", str(native)), ("unset", None), ("restored", str(native))):
    env = dict(environment)
    if model is not None:
        env["GEOMETRY_MODEL_BASE"] = model
    assert digest(native) == identity["binary_sha256"]
    assert digest(root / script) == identity["test_file_sha256"]
    result = record(label, command, env, 300)
    text = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    match = re.search(r"^(not ok|ok) \d+ - R13_H15 ", text, re.MULTILINE)
    passed = label != "unset"
    checks = {
        "exit": result.returncode == (0 if passed else 1),
        "named_h15": bool(match and match.group(1) == ("ok" if passed else "not ok")),
        "one_executed": bool(re.search(r"^# pass " + str(int(passed)) + r"$", text, re.MULTILINE) and
                             re.search(r"^# fail " + str(int(not passed)) + r"$", text, re.MULTILINE)),
        "outer_message": passed or "R13_NATIVE_PREPARE_LATE_OWNER" in text,
    }
    runs.append({"label": label, "GEOMETRY_MODEL_BASE": model, "exit": result.returncode, "checks": checks,
                 "inner_model_required_message": "R13_STORE_NATIVE_MODEL_BASE_REQUIRED" in text})
summary = {"identity": identity, "build_exit": build.returncode, "runs": runs,
           "unchanged": git("rev-parse", "HEAD") == target and not git("status", "--porcelain=v1"),
           "final_binary_sha256": digest(native)}
(report / "report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
assert all(all(run["checks"].values()) for run in runs)
assert summary["unchanged"] and summary["final_binary_sha256"] == identity["binary_sha256"]
