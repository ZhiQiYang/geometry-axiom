#!/usr/bin/env python3
"""Run named PR353 codec/staging mutations in an isolated byte copy.
This is Node/VM evidence, not Chrome/native acceptance. Runtime failures are
blocked; only a completed named assertion failure after green control is killed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
INPUTS = [
    "geometry-web/project-store.js", "geometry-web/feature-attachments.js",
    "geometry-web/scenario-catalog.js", "geometry-web/source-plane.js",
    "geometry-web/evidence-links.js", "geometry-web/rule-case-data.js",
    "geometry-web/reference-display.js", "geometry-web/scenario-snapshots.js",
    "geometry-web/reference-workspace.js", "geometry-web/grid-system-workspace.js",
    "geometry-web/vendor/fflate/umd/index.js",
    "tests/test_pr353_compatibility.js", "tests/pr353_legacy_reader.js",
    "tests/pr353_compat_mutations.json", "tests/run_pr353_compat_mutations.py",
]

def digest(value):
    return hashlib.sha256(value).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--node", default="node")
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error("--out must be an empty directory")
    out.mkdir(parents=True, exist_ok=True)
    tree = out / "source"
    original = {}
    for name in INPUTS:
        value = (ROOT / name).read_bytes()
        original[name] = value
        target = tree / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    receipt = {"schema": "pr353-node-mutation-receipt/1",
               "level": "Node codec + ReferenceWorkspace VM; no browser/native run",
               "inputs": [{"file": name, "bytes": len(value), "sha256": digest(value)}
                          for name, value in original.items()],
               "runs": [], "mutations": []}
    env = os.environ.copy()
    try:
        legacy = out / "legacy"
        command = [args.node, "tests/pr353_legacy_reader.js", "--materialize", str(legacy)]
        materialize = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                     capture_output=True, timeout=30)
        (out / "legacy-materialize.log").write_text(materialize.stdout + materialize.stderr, encoding="utf-8")
        if materialize.returncode != 0:
            raise RuntimeError("fixed legacy reader unavailable; see legacy-materialize.log")
        receipt["legacy"] = json.loads(materialize.stdout)
        env["GEOMETRY_PR353_LEGACY_ROOT"] = str(legacy)
        def run(label, pattern=None):
            command = [args.node, "--test-reporter=tap"]
            if pattern:
                command.append("--test-name-pattern=^" + pattern + " ")
            command.append("tests/test_pr353_compatibility.js")
            try:
                result = subprocess.run(command, cwd=tree, env=env, text=True,
                                        capture_output=True, timeout=60)
                output = result.stdout + result.stderr
                code = result.returncode
            except subprocess.TimeoutExpired as error:
                output = str(error)
                code = None
            log = out / (label + ".log")
            log.write_text(output, encoding="utf-8")
            numbers = {key: int(value) for key, value in
                       re.findall(r"^# (tests|pass|fail|cancelled|skipped|todo) (\d+)$", output, re.M)}
            row = {"label": label, "command": command, "cwd": str(tree), "exit": code,
                   "counts": numbers, "log": log.name, "logSHA256": digest(output.encode())}
            receipt["runs"].append(row)
            return row, output
        def green(row, total):
            counts = row["counts"]
            return row["exit"] == 0 and counts.get("tests") == total and counts.get("pass") == total and all(counts.get(key) == 0 for key in ["fail", "cancelled", "skipped", "todo"])
        baseline, _ = run("baseline")
        if not green(baseline, 10):
            raise RuntimeError("baseline is not exactly 10/10; no mutation credit")
        spec = json.loads((tree / "tests/pr353_compat_mutations.json").read_text())
        for mutation in spec["mutations"]:
            control, _ = run(mutation["id"] + "-control", mutation["case"])
            if not green(control, 1):
                raise RuntimeError("named baseline did not complete: " + mutation["id"])
            touched = []
            try:
                for change in mutation["changes"]:
                    target = tree / change["file"]
                    text = target.read_text(encoding="utf-8")
                    if text.count(change["before"]) != 1:
                        raise RuntimeError("mutation anchor must occur exactly once: " + mutation["id"])
                    touched.append(change["file"])
                    target.write_text(text.replace(change["before"], change["after"], 1), encoding="utf-8", newline="\n")
                altered, output = run(mutation["id"] + "-mutant", mutation["case"])
                counts = altered["counts"]
                killed = altered["exit"] == 1 and counts.get("tests") == 1 and counts.get("fail") == 1 and counts.get("pass") == 0 and all(counts.get(key) == 0 for key in ["cancelled", "skipped", "todo"]) and "ERR_ASSERTION" in output and re.search(r"^not ok \d+ - " + re.escape(mutation["case"]) + r" ", output, re.M) is not None
            finally:
                for name in touched:
                    (tree / name).write_bytes(original[name])
            restored, _ = run(mutation["id"] + "-restored", mutation["case"])
            status = "killed" if killed and green(restored, 1) else "survived" if altered["exit"] == 0 else "blocked"
            receipt["mutations"].append({"id": mutation["id"], "case": mutation["case"],
                                          "status": status, "restored": green(restored, 1)})
            if status != "killed":
                raise RuntimeError("mutation was not a completed assertion kill + restoration: " + mutation["id"])
        final, _ = run("restored-full")
        if not green(final, 10):
            raise RuntimeError("restored full suite not 10/10")
        if any((tree / name).read_bytes() != value or (ROOT / name).read_bytes() != value
               for name, value in original.items()):
            raise RuntimeError("source bytes changed outside isolated mutation")
        receipt["status"] = "pass"
        code = 0
    except Exception as error:
        receipt["status"] = "blocked"
        receipt["error"] = str(error)
        code = 2
    (out / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "mutations": receipt["mutations"],
                      "receipt": str(out / "receipt.json"),
                      **({"error": receipt["error"]} if "error" in receipt else {})},
                     ensure_ascii=False))
    return code

if __name__ == "__main__":
    sys.exit(main())
