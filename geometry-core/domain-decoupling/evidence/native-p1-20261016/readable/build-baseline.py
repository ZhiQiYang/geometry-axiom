#!/usr/bin/env python3
"""P1 baseline adapter receipt. Never invokes run_all or modifies source/expected."""
from __future__ import annotations
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE = "a898ad6e12707104568679591fe1b21804bfc3df"
ROOT = Path("/var/tmp/geo261-baseline-a898ad6e")
EVIDENCE = Path("/mnt/d/geometry-axiom-work/geo261-evidence/p1")
OUT = EVIDENCE / "baseline-adapters-a898ad6e"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def command(args):
    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()

def manifest(path):
    files = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
    rows = {os.fsdecode(name): sha(ROOT / os.fsdecode(name)) for name in files if name}
    path.write_text(json.dumps(rows, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return rows

def main():
    OUT.mkdir(parents=True, exist_ok=False)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    actual = command(["git", "rev-parse", "HEAD"])
    status_before = command(["git", "status", "--porcelain=v1"])
    if actual != SOURCE or status_before:
        raise RuntimeError("baseline source is not exact clean pinned main")
    runner_paths = [EVIDENCE / name for name in ("prepare-baseline.sh", "baseline-namespace.sh", "build-baseline.py")]
    lock_script = Path("/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_locked3.sh")
    runner_paths.append(lock_script)
    runners_before = {str(path): sha(path) for path in runner_paths}
    (OUT / "status-before.txt").write_text(status_before, encoding="utf-8")
    before = manifest(OUT / "source-before.json")
    tools = {name: command(cmd) for name, cmd in {
        "python": ["python", "--version"], "python3": ["python3", "--version"],
        "gcc": ["gcc", "--version"], "git": ["git", "--version"],
        "node": ["node", "--version"], "chrome": ["google-chrome", "--version"],
        "stack_kib": ["bash", "-c", "ulimit -s"],
    }.items()}
    build_cmd = ["python3", "-u", "tests/binaries.py", "build", "model-base", "bridge"]
    with (OUT / "build.log").open("wb") as log:
        built = subprocess.run(build_cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    (OUT / "build-exit.txt").write_text(str(built.returncode) + "\n", encoding="ascii")
    status_cmd = ["python3", "tests/binaries.py", "status", "model-base", "bridge"]
    with (OUT / "binary-status.log").open("wb") as log:
        checked = subprocess.run(status_cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    registry_spec = importlib.util.spec_from_file_location("geo261_baseline_binaries", ROOT / "tests/binaries.py")
    registry = importlib.util.module_from_spec(registry_spec)
    registry_spec.loader.exec_module(registry)
    records = {}
    for name in ("model-base", "bridge"):
        info = registry.inspect_one(registry.BY_NAME[name])
        sidecar = info.path.with_name(info.path.name + registry.SIDECAR_SUFFIX)
        if sidecar.exists():
            shutil.copy2(sidecar, OUT / sidecar.name)
        records[name] = {"state": info.state, "reason": info.reason, "path": str(info.path),
                         "persistent_host_path": str(ROOT / ".git/geo261-environment/tmp" / info.path.relative_to("/tmp")),
                         "sha256": sha(info.path) if info.path.exists() else None,
                         "sidecar_sha256": sha(sidecar) if sidecar.exists() else None}
    producer = EVIDENCE / "producer/produce_fixtures_v3.py"
    producer_out = EVIDENCE / "compatibility-baseline-v1"
    producer_cmd = ["python3", "-u", str(producer), "--root", str(ROOT),
                    "--base", "/tmp/geometry-tests/model-base", "--out", str(producer_out)]
    producer_code = None
    if built.returncode == checked.returncode == 0 and all(item["state"] == "fresh" for item in records.values()):
        with (OUT / "producer.log").open("wb") as log:
            produced = subprocess.run(producer_cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        producer_code = produced.returncode
        (OUT / "producer-exit.txt").write_text(str(producer_code) + "\n", encoding="ascii")
    status_after = command(["git", "status", "--porcelain=v1"])
    head_after = command(["git", "rev-parse", "HEAD"])
    (OUT / "status-after.txt").write_text(status_after, encoding="utf-8")
    after = manifest(OUT / "source-after.json")
    runners_after = {str(path): sha(path) for path in runner_paths}
    ok = (built.returncode == checked.returncode == producer_code == 0 and before == after and not status_after and head_after == SOURCE
          and runners_before == runners_after and all(item["state"] == "fresh" for item in records.values()))
    summary = {
        "kind": "baseline-native-adapter-preparation-only", "source": SOURCE, "checkout": str(ROOT),
        "started_utc": started, "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "shared_lock": "/run/lock/ga-wsl-v3.lock", "lock_holder_at_run": Path("/run/lock/ga-wsl-v3.holder").read_text(),
        "isolation": "private mount and network namespaces inside shared lock; private persistent /tmp bound from checkout .git/geo261-environment/tmp",
        "tools": tools, "path": os.environ["PATH"], "build_command": build_cmd, "status_command": status_cmd,
        "build_exit": built.returncode, "binary_status_exit": checked.returncode,
        "producer_command": producer_cmd, "producer_exit": producer_code, "producer_script_sha256": sha(producer),
        "producer_outputs": {path.name: sha(path) for path in sorted(producer_out.glob("*")) if path.is_file()},
        "source_files": len(before), "source_unchanged": before == after,
        "head_after": head_after, "head_unchanged": head_after == SOURCE,
        "runner_scripts_sha256": runners_before, "runner_scripts_unchanged": runners_before == runners_after,
        "source_before_sha256": sha(OUT / "source-before.json"), "source_after_sha256": sha(OUT / "source-after.json"),
        "axiom_lf_sha256": hashlib.sha256((ROOT / "公理層.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "binaries": records, "full_test_suite_executed": False, "producer_fixtures_executed": producer_code is not None,
        "logs_sha256": {path.name: sha(path) for path in sorted(OUT.glob("*.log"))},
        "exit": 0 if ok else 1,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "exit.txt").write_text(str(summary["exit"]) + "\n", encoding="ascii")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary["exit"]

if __name__ == "__main__":
    sys.exit(main())
