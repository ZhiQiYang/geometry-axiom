#!/usr/bin/env python3
"""Fixed N1b source archive and original 20-test evidence, independent of N1a."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

SOURCE = "51e9045b43078a77383afdaf5db379117ffc8871"
BASELINE = Path("/var/tmp/geo261-baseline-a898ad6e")
EVIDENCE = Path("/mnt/d/geometry-axiom-work/geo261-evidence/p1")
OUT = EVIDENCE / "native-geometry-51e9045b-v1"
ROOT = BASELINE / ".git/geo261-candidates/native-geometry-51e9045b"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest():
    return {str(path.relative_to(ROOT)): sha(path) for path in sorted(ROOT.rglob("*")) if path.is_file()}

def main():
    OUT.mkdir(exist_ok=False)
    ROOT.mkdir(parents=True, exist_ok=False)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    archive = ROOT.parent / "native-geometry-51e9045b.tar"
    subprocess.run(["git", "-C", str(BASELINE), "archive", "--format=tar", "--output=" + str(archive), SOURCE], check=True)
    with tarfile.open(archive) as source:
        source.extractall(ROOT, filter="data")
    before = manifest()
    (OUT / "source-before.json").write_text(json.dumps(before, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    private_tmp = BASELINE / ".git/geo261-native-geometry-tmp"
    private_tmp.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["TMPDIR"] = str(private_tmp)
    for key in ("GEOMETRY_MODEL_BASE", "GEOMETRY_TEST_BRIDGE", "GEOMETRY_ENGINEERING_BRIDGE", "GEOMETRY_TEST_ENGINEERING_JSON", "GEOMETRY_TEST_CORE"):
        env.pop(key, None)
    command = ["python3", "-u", str(EVIDENCE / "exercise-native-geometry.py"), str(ROOT), str(OUT)]
    with (OUT / "unittest.log").open("wb") as log:
        run = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    after = manifest()
    (OUT / "source-after.json").write_text(json.dumps(after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"kind": "fixed-commit-targeted-native-geometry", "source": SOURCE, "source_archive": str(archive),
               "archive_sha256": sha(archive), "source_root": str(ROOT), "command": command,
               "started_utc": started, "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "private_tmp": str(private_tmp), "shared_lock_holder": Path("/run/lock/ga-wsl-v3.holder").read_text(),
               "test_exit": run.returncode, "source_unchanged": before == after,
               "source_before_sha256": sha(OUT / "source-before.json"), "source_after_sha256": sha(OUT / "source-after.json"),
               "source_files": len(before), "log_sha256": sha(OUT / "unittest.log"),
               "full_suite_executed": False, "browser_executed": False,
               "runner_sha256": {name: sha(EVIDENCE / name) for name in ("native-geometry-namespace.sh", "run-native-geometry.py", "exercise-native-geometry.py")},
               "exit": 0 if run.returncode == 0 and before == after else 1}
    if (OUT / "test-result.json").exists():
        summary["test_result"] = json.loads((OUT / "test-result.json").read_text())
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "exit.txt").write_text(str(summary["exit"]) + "\n", encoding="ascii")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary["exit"]

if __name__ == "__main__":
    sys.exit(main())
