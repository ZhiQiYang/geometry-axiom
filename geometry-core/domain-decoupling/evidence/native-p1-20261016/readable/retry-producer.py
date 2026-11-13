#!/usr/bin/env python3
"""Retry only producer receipt serialization; preserve original failed outputs."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path("/var/tmp/geo261-baseline-a898ad6e")
EVIDENCE = Path("/mnt/d/geometry-axiom-work/geo261-evidence/p1")
OUT = EVIDENCE / "producer-retry-v2"
FIXTURES = EVIDENCE / "compatibility-baseline-v2"
PRODUCER = EVIDENCE / "producer/produce_fixtures_v4.py"
SOURCE = "a898ad6e12707104568679591fe1b21804bfc3df"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest():
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
    return {name.decode(): sha(ROOT / name.decode()) for name in names if name}

def head():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

def main():
    OUT.mkdir(exist_ok=False)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    before = manifest()
    if head() != SOURCE:
        raise RuntimeError("baseline HEAD changed")
    spec = importlib.util.spec_from_file_location("producer_retry_binaries", ROOT / "tests/binaries.py")
    registry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registry)
    states_before = {name: registry.inspect_one(registry.BY_NAME[name]).state for name in ("model-base", "bridge")}
    if set(states_before.values()) != {"fresh"}:
        raise RuntimeError("baseline adapters lost freshness")
    command = ["python3", "-u", str(PRODUCER), "--root", str(ROOT), "--base", "/tmp/geometry-tests/model-base", "--out", str(FIXTURES)]
    with (OUT / "producer.log").open("wb") as log:
        run = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    after = manifest()
    states_after = {name: registry.inspect_one(registry.BY_NAME[name]).state for name in ("model-base", "bridge")}
    common = {path.name: sha(path) == sha(FIXTURES / path.name) for path in sorted((EVIDENCE / "compatibility-baseline-v1").glob("*.json")) if (FIXTURES / path.name).exists()}
    source_unchanged = before == after and head() == SOURCE
    (OUT / "source-before.json").write_text(json.dumps(before, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "source-after.json").write_text(json.dumps(after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"kind": "baseline-producer-receipt-retry", "source": SOURCE,
               "reason": "original producer serialized historical version tuples through a JSON-only canonicalizer; v4 converts those pairs to arrays",
               "started_utc": started, "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "shared_lock_holder": Path("/run/lock/ga-wsl-v3.holder").read_text(), "command": command,
               "producer_script_sha256": sha(PRODUCER), "producer_exit": run.returncode,
               "adapters_before": states_before, "adapters_after": states_after, "source_unchanged": source_unchanged,
               "source_before_sha256": sha(OUT / "source-before.json"), "source_after_sha256": sha(OUT / "source-after.json"),
               "original_partial_fixture_byte_equality": common,
               "fixture_sha256": {path.name: sha(path) for path in sorted(FIXTURES.glob("*")) if path.is_file()},
               "log_sha256": sha(OUT / "producer.log"), "full_suite_executed": False,
               "exit": 0 if run.returncode == 0 and source_unchanged and set(states_after.values()) == {"fresh"} and len(common) == 11 and all(common.values()) else 1}
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "exit.txt").write_text(str(summary["exit"]) + "\n", encoding="ascii")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary["exit"]

if __name__ == "__main__":
    sys.exit(main())
