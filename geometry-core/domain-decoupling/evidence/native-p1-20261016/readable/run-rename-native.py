#!/usr/bin/env python3
"""Targeted unstaged rename evidence; not a candidate or browser suite receipt."""
from __future__ import annotations
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path("/mnt/d/geometry-axiom-work/geo261-grid-rename")
BASELINE = Path("/var/tmp/geo261-baseline-a898ad6e")
RENAME_COMMIT = "2f015dfd62779baba066f503f21422f8472a0ae8"
OUT = Path("/mnt/d/geometry-axiom-work/geo261-evidence/p1/grid-rename-native-v1")
REQUIRED = ["geometry-web/grid-inspector.js", "tests/fixtures/grid_inspector_command.cjs", "tests/test_grid_inspector_contract.py"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest():
    files = set(REQUIRED)
    files.update(str(path.relative_to(ROOT)).replace(os.sep, "/") for path in (ROOT / "tests").glob("*.py"))
    return {name: sha(ROOT / name) for name in sorted(files)}

def source_head():
    git_pointer = (ROOT / ".git").read_text(encoding="utf-8").strip()
    if not git_pointer.startswith("gitdir: "):
        raise RuntimeError("expected the rename managed worktree Git pointer")
    raw = git_pointer[8:].replace("\\", "/")
    git_dir = "/mnt/" + raw[0].lower() + raw[2:] if len(raw) > 2 and raw[1:3] == ":/" else raw
    return subprocess.check_output(["git", "--no-optional-locks", "--git-dir=" + git_dir,
                                    "--work-tree=" + str(ROOT), "rev-parse", "HEAD"], text=True).strip()

def main():
    OUT.mkdir(parents=True, exist_ok=False)
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    head_before = source_head()
    if head_before != RENAME_COMMIT:
        raise RuntimeError("rename worktree HEAD differs from the frozen candidate commit")
    before = manifest()
    expected = json.loads((OUT.parent / "grid-rename-expected-sources.json").read_text(encoding="utf-8"))
    if {name: before[name] for name in REQUIRED} != expected:
        raise RuntimeError("rename sources differ from worker's final frozen SHA-256 receipt")
    spec = importlib.util.spec_from_file_location("rename_native_binaries", ROOT / "tests/binaries.py")
    registry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registry)
    fresh = registry.inspect_one(registry.BY_NAME["bridge"], "/tmp/geometry-tests/bridge")
    if fresh.state != "fresh":
        raise RuntimeError("main bridge is not fresh for rename working-tree sources: " + fresh.reason)
    cmd = ["python3", "-u", "-m", "unittest", "-v", "tests.test_grid_inspector_contract", "tests.test_infinite_grid_contract"]
    with (OUT / "unittest.log").open("wb") as log:
        result = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    after = manifest()
    head_after = source_head()
    (OUT / "source-before.json").write_text(json.dumps(before, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "source-after.json").write_text(json.dumps(after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "kind": "commit-targeted-native-rename-checks", "baseline_main": "a898ad6e12707104568679591fe1b21804bfc3df",
        "rename_commit": head_before, "rename_head_unchanged": head_before == head_after,
        "baseline_checkout": str(BASELINE), "working_tree": str(ROOT),
        "command": cmd, "started_utc": start, "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "bridge_path": str(fresh.path), "bridge_fresh": fresh.state, "bridge_sha256": sha(fresh.path),
        "shared_lock_holder": Path("/run/lock/ga-wsl-v3.holder").read_text(),
        "unittest_exit": result.returncode, "sources_unchanged": before == after,
        "required_source_sha256": {name: before[name] for name in REQUIRED},
        "source_before_sha256": sha(OUT / "source-before.json"), "source_after_sha256": sha(OUT / "source-after.json"),
        "log_sha256": sha(OUT / "unittest.log"), "full_suite_executed": False, "browser_executed": False,
        "exit": 0 if result.returncode == 0 and before == after and head_before == head_after else 1,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "exit.txt").write_text(str(summary["exit"]) + "\n", encoding="ascii")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary["exit"]

if __name__ == "__main__":
    sys.exit(main())
