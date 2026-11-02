#!/usr/bin/env python3
"""Record one unchanged task command with complete raw streams outside source."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument("--name", required=True)
p.add_argument("--cwd", required=True)
p.add_argument("command", nargs=argparse.REMAINDER)
a = p.parse_args()
argv = a.command[1:] if a.command[:1] == ["--"] else a.command
out = Path(__file__).resolve().parent / "commands" / a.name
out.mkdir(parents=True, exist_ok=False)
request = {
    "argv": argv,
    "cwd": a.cwd,
    "startedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "environment": {k: os.environ.get(k) for k in (
        "TMPDIR", "TMP", "TEMP", "GEOMETRY_TEST_BRIDGE", "GEOMETRY_MODEL_BASE",
        "GEOMETRY_TEST_URL", "PYTHONOPTIMIZE", "CC", "CFLAGS", "LDFLAGS")},
}
(out / "REQUEST.json").write_text(json.dumps(request, indent=2) + "\n")
started = time.monotonic()
with (out / "stdout.bin").open("wb") as stdout, (out / "stderr.bin").open("wb") as stderr:
    proc = subprocess.run(argv, cwd=a.cwd, stdout=stdout, stderr=stderr, check=False)
result = {
    "actualProcessReturncode": proc.returncode,
    "elapsedSeconds": time.monotonic() - started,
    "endedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "streams": {},
}
for name in ("stdout.bin", "stderr.bin"):
    raw = (out / name).read_bytes()
    result["streams"][name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
(out / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"name": a.name, "exit": proc.returncode, "elapsedSeconds": result["elapsedSeconds"], "stdoutBytes": result["streams"]["stdout.bin"]["bytes"], "stderrBytes": result["streams"]["stderr.bin"]["bytes"]}))
raise SystemExit(proc.returncode)
