#!/usr/bin/env python3
"""Run a selected Python suite set from a frozen Git archive, without native binaries.

Example:
  python tests/geometry_kernel_receipt.py --suite-set py2 --source <full-commit> --out <TEMP-dir>

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
PY1_SUITES = {
    "test_geometry_kernel_compatibility": 1,
    "test_geometry_kernel_geometry": 20,
    "test_geometry_kernel_isolation": 2,
}
PY2_SUITES = {**PY1_SUITES, "test_geometry_kernel_graph": 23,
              "test_geometry_kernel_runtime": 2, "test_geometry_kernel_transactions": 31,
              "test_geometry_kernel_session": 4, "test_geometry_host_world": 8}
# Historical presets reproduce their fixed receipts; new source counts belong
# in a new preset rather than silently rewriting an earlier evidence command.
TYPED_SOURCE_SUITES = {**PY2_SUITES, "test_geometry_kernel_graph": 27,
                       "test_geometry_kernel_runtime": 4, "test_geometry_host_native": 22}
SUITE_SETS = {"py1": PY1_SUITES, "py2": PY2_SUITES,
              "native-host": {"test_geometry_host_native": 22},
              "capability-phase": {"test_geometry_kernel_runtime": 4},
              "typed-sources": TYPED_SOURCE_SUITES}


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--suite-set", choices=tuple(SUITE_SETS), default="py1")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.source):
        parser.error("--source must be a complete commit SHA")
    source = git("rev-parse", "--verify", args.source + "^{commit}").decode().strip()
    suites = SUITE_SETS[args.suite_set]
    paths = ("geometry-core/geometry_kernel", "geometry-core/modeling", "tests/__init__.py",
             "tests/_unittest_runner.py", "tests/binaries.py", *(f"tests/{name}.py" for name in suites))
    if args.suite_set != "py1":
        paths += ("geometry-app/geometry_app", "geometry-templates/woodworking/geometry_woodworking")
    archive = git("archive", "--format=zip", source, *paths)
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    records = []
    failed = False
    with tempfile.TemporaryDirectory(prefix="geometry-" + args.suite_set + "-frozen-") as directory:
        frozen = Path(directory).resolve()
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            for name in bundle.namelist():
                if not (frozen / name).resolve().is_relative_to(frozen):
                    raise ValueError("Archive entry escaped its frozen root")
            bundle.extractall(frozen)
        inventory = [{"path": p.relative_to(frozen).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                     for p in sorted(frozen.rglob("*")) if p.is_file()]
        for name, expected in suites.items():
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
        "schema": "geo261-python-receipt/1", "suite_set": args.suite_set, "utc": datetime.now(timezone.utc).isoformat(),
        "source": source, "source_tree": git("show", "-s", "--format=%T", source).decode().strip(),
        "worktree_dirty": bool(git("status", "--porcelain")), "execution_source": "frozen git archive",
        "runner_sha256_lf": hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "python": sys.version, "inventory": inventory, "suites": records, "native_executed": False,
        "expected_total": sum(suites.values()), "success": not failed,
        "scope": "Shared exact geometry and selected graph/host/candidate suites; no real native fixture replay, full native source DTO or complete domain-decoupling claim",
    }
    (output / "summary.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source": source, "success": not failed, "expected_total": sum(suites.values()), "receipt": str(output / "summary.json")}, ensure_ascii=False))
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
