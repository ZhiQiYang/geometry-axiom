#!/usr/bin/env python3
"""Archive a fixed native candidate and preserve its targeted test receipt."""
from __future__ import annotations
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

SOURCE = "ab90a56df488b0cd38d5e6f9df1ed5597a8e126e"
BASELINE = Path("/var/tmp/geo261-baseline-a898ad6e")
EVIDENCE = Path("/mnt/d/geometry-axiom-work/geo261-evidence/p1")
OUT = EVIDENCE / "native-kernel-ab90a56d-v1"
SOURCE_ROOT = BASELINE / ".git/geo261-candidates/native-kernel-ab90a56d"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest():
    return {str(path.relative_to(SOURCE_ROOT)): sha(path) for path in sorted(SOURCE_ROOT.rglob("*")) if path.is_file()}

def main():
    OUT.mkdir(parents=True, exist_ok=False)
    SOURCE_ROOT.mkdir(parents=True, exist_ok=False)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    archive = SOURCE_ROOT.parent / "native-kernel-ab90a56d.tar"
    subprocess.run(["git", "-C", str(BASELINE), "archive", "--format=tar", "--output=" + str(archive), SOURCE], check=True)
    with tarfile.open(archive) as source:
        source.extractall(SOURCE_ROOT, filter="data")
    before = manifest()
    (OUT / "source-before.json").write_text(json.dumps(before, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    private_tmp = BASELINE / ".git/geo261-native-tmp"
    private_tmp.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["TMPDIR"] = str(private_tmp)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # This standalone suite builds its own objects and never consumes a baseline override.
    for key in ("GEOMETRY_MODEL_BASE", "GEOMETRY_TEST_BRIDGE", "GEOMETRY_ENGINEERING_BRIDGE", "GEOMETRY_TEST_ENGINEERING_JSON", "GEOMETRY_TEST_CORE"):
        env.pop(key, None)
    command = ["python3", "-u", str(EVIDENCE / "exercise-native-kernel.py"), str(SOURCE_ROOT), str(OUT)]
    with (OUT / "unittest.log").open("wb") as log:
        run = subprocess.run(command, cwd=SOURCE_ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    after = manifest()
    (OUT / "source-after.json").write_text(json.dumps(after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"kind": "fixed-commit-targeted-native-kernel", "source": SOURCE, "source_archive": str(archive),
               "archive_sha256": sha(archive), "source_root": str(SOURCE_ROOT), "command": command,
               "started_utc": started, "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "private_tmp": str(private_tmp), "shared_lock_holder": Path("/run/lock/ga-wsl-v3.holder").read_text(),
               "test_exit": run.returncode, "source_unchanged": before == after,
               "source_before_sha256": sha(OUT / "source-before.json"), "source_after_sha256": sha(OUT / "source-after.json"),
               "source_files": len(before), "log_sha256": sha(OUT / "unittest.log"),
               "full_suite_executed": False, "browser_executed": False,
               "runner_sha256": {name: sha(EVIDENCE / name) for name in ("run-native-kernel.py", "exercise-native-kernel.py")},
               "exit": 0 if run.returncode == 0 and before == after else 1}
    if (OUT / "test-result.json").exists():
        summary["test_result"] = json.loads((OUT / "test-result.json").read_text())
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "exit.txt").write_text(str(summary["exit"]) + "\n", encoding="ascii")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary["exit"]

if __name__ == "__main__":
    sys.exit(main())
