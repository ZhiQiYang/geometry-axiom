#!/usr/bin/env python3
"""Run independent targeted stages under one already-held shared lock."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

OUT = Path("/mnt/d/geometry-axiom-work/geo261-evidence/p1")
stages = ("build-baseline.py", "run-rename-native.py", "run-native-kernel.py")
receipt = OUT / "stage-results.json"
if receipt.exists():
    raise SystemExit("Preserve the completed stage receipt; choose a new run for retries")
rows = []
for name in stages:
    script = OUT / name
    log = OUT / (script.stem + "-console.log")
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with log.open("xb") as output:
        run = subprocess.Popen(["python3", "-u", str(script)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in iter(run.stdout.readline, b""):
            output.write(line)
            output.flush()
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
        code = run.wait()
    rows.append({"script": str(script), "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
                 "command": ["python3", "-u", str(script)], "started_utc": started,
                 "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "exit": code,
                 "console_log": str(log), "console_log_sha256": hashlib.sha256(log.read_bytes()).hexdigest()})
receipt.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
sys.exit(0 if all(row["exit"] == 0 for row in rows) else 1)
