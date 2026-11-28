#!/usr/bin/env python3
"""Bounded 0/1/0 source withdrawal of the raw key/kind/id guard only."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-artifacts", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    here, out = Path(__file__).resolve().parent, args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    original = (here / "native_projection.py").read_text(encoding="utf-8")
    before = 'assert uint(numeric_id) and node.get("key") == expected_key and node.get("kind") == kind and numeric_id == identifier, "U476_NATIVE_TYPED_ROOT_MISMATCH"'
    after = 'assert uint(numeric_id), "U476_NATIVE_TYPED_ROOT_MISMATCH"'
    assert original.count(before) == 1, "U476_WITHDRAW_ANCHOR"
    mutant = original.replace(before, after)
    (out / "withdrawal.patch").write_text("".join(difflib.unified_diff(original.splitlines(True), mutant.splitlines(True),
            fromfile="a/native_projection.py", tofile="b/native_projection.py")), encoding="utf-8", newline="\n")
    source = out / "native_projection.py"
    results = []
    for name, text, wanted in (("baseline", original, 0), ("withdrawn", mutant, 1), ("restored", original, 0)):
        source.write_text(text, encoding="utf-8", newline="\n")
        command = [sys.executable, str(here / "native_root_probe.py"), "--native-artifacts", str(args.native_artifacts.resolve()), "--projection", str(source)]
        start = time.monotonic()
        result = subprocess.run(command, capture_output=True, timeout=30, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        (out / (name + ".stdout.txt")).write_bytes(result.stdout)
        (out / (name + ".stderr.txt")).write_bytes(result.stderr)
        receipt = {"command": command, "exit": result.returncode, "timeoutSeconds": 30,
                   "elapsedSeconds": time.monotonic() - start,
                   "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        (out / (name + ".receipt.json")).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
        assert result.returncode == wanted, ("U476_WITHDRAW_EXIT", name, result.returncode, result.stderr.decode())
        if name == "withdrawn":
            assert b"U476_ROOT_GUARD_WRONG_FAILURE" in result.stderr or b"U476_ROOT_GUARD_ACCEPTED_CORRUPTION" in result.stderr, "U476_WITHDRAW_WRONG_RED"
        results.append(receipt)
    summary = {"name": "M_U476_NATIVE_RAW_ROOT_TRIPLE", "exits": [entry["exit"] for entry in results],
               "researchOnly": True, "sourceRestored": source.read_text() == original, "results": results}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"name": summary["name"], "exits": summary["exits"], "sourceRestored": summary["sourceRestored"]}))


if __name__ == "__main__":
    main()
