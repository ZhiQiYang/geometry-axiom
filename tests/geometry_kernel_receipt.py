#!/usr/bin/env python3
"""Run the PY1 suites against a frozen Git archive, without native binaries.

Example:
  python tests/geometry_kernel_receipt.py --source <full-commit> --out <TEMP-dir>

The checked-out tree may contain later WIP: the actual executable input comes
only from the requested commit. Per-suite discovery and raw logs come from the
repository's unchanged _unittest_runner.py, also archived at that commit.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SUITES = {
    "test_geometry_kernel_compatibility": 1,
    "test_geometry_kernel_geometry": 20,
    "test_geometry_kernel_isolation": 2,
}
PATHS = ("geometry-core/geometry_kernel", "geometry-core/modeling", "tests/__init__.py",
         "tests/_unittest_runner.py", "tests/binaries.py", *(f"tests/{name}.py" for name in SUITES))


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.source):
        parser.error("--source must be a complete commit SHA")
    source = git("rev-parse", "--verify", args.source + "^{commit}").decode().strip()
    archive = git("archive", "--format=zip", source, *PATHS)
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    records = []
    failed = False
    with tempfile.TemporaryDirectory(prefix="geometry-py1-frozen-") as directory:
        frozen = Path(directory).resolve()
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            for name in bundle.namelist():
                if not (frozen / name).resolve().is_relative_to(frozen):
                    raise ValueError("Archive entry escaped its frozen root")
            bundle.extractall(frozen)
        inventory = [{"path": p.relative_to(frozen).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                     for p in sorted(frozen.rglob("*")) if p.is_file()]
        for name, expected in SUITES.items():
            result_path = output / (name + ".json")
            log_path = output / (name + ".log")
            command = [sys.executable, str(frozen / "tests/_unittest_runner.py"),
                       str(frozen / "tests" / (name + ".py")), "--json-out", str(result_path), "--log", str(log_path)]
            environment = {key: value for key, value in os.environ.items() if not key.startswith("GEOMETRY_")}
            process = subprocess.run(command, cwd=frozen, env=environment, text=True, capture_output=True, timeout=120)
            (output / (name + ".process.log")).write_text(process.stdout + process.stderr, encoding="utf-8")
            result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {}
            record = {"suite": name, "command": command, "cwd": str(frozen), "exit": process.returncode,
                      "expected": expected, "result": result, "raw_log": str(log_path)}
            records.append(record)
            failed |= process.returncode != 0 or result.get("total") != expected or result.get("skipped", 0) != 0
    receipt = {
        "schema": "geo261-python-py1-receipt/1", "utc": datetime.now(timezone.utc).isoformat(),
        "source": source, "source_tree": git("show", "-s", "--format=%T", source).decode().strip(),
        "worktree_dirty": bool(git("status", "--porcelain")), "execution_source": "frozen git archive",
        "runner_sha256_lf": hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "python": sys.version, "inventory": inventory, "suites": records, "native_executed": False,
        "expected_total": sum(SUITES.values()), "success": not failed,
        "scope": "Shared exact geometry, kernel-only installation, two shared-source negative controls; no native fixture replay or complete graph-decoupling claim",
    }
    (output / "summary.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source": source, "success": not failed, "expected_total": 23, "receipt": str(output / "summary.json")}, ensure_ascii=False))
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
