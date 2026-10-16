"""Non-destructive red/green proof for the compact grid name-only serializer.

Only TEMP source copies are mutated. Optional --native repeats the native rename
matrix using the explicitly supplied, verified GEOMETRY_TEST_BRIDGE.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--native", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    source = ROOT / "geometry-web/grid-inspector.js"
    original = source.read_text(encoding="utf-8")
    absent = "const stagger=Object.hasOwn(d,'stagger') || d.parameterRefs?.stagger ? ` stagger ${token('stagger')}` : '';"
    assert original.count(absent) == 1
    assert original.count("${token('stagger')}") == 1
    variants = {"baseline": original,
        "omit-stagger": original.replace(absent, "const stagger='';"),
        "freeze-stagger-reference": original.replace("${token('stagger')}", "${d.stagger}"),
        "restored": original}
    suites = {"vm": ["node", "--test", "--test-reporter=tap", "tests/test_grid_inspector_command.js"]}
    if args.native:
        assert os.environ.get("GEOMETRY_TEST_BRIDGE"), "native mutation requires an explicit verified bridge"
        import sys
        suites["native"] = [sys.executable, "-m", "unittest", "tests.test_grid_inspector_contract"]
    results = []
    with tempfile.TemporaryDirectory(prefix="geometry-grid-rename-mutation-") as tmp:
        for label, code in variants.items():
            candidate = Path(tmp) / (label + ".js")
            candidate.write_text(code, encoding="utf-8")
            for suite, command in suites.items():
                env = {**os.environ, "GEOMETRY_GRID_INSPECTOR_SOURCE": str(candidate)}
                run = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
                log = args.out / f"{label}-{suite}.log"
                log.write_bytes(run.stdout + run.stderr)
                expected = 0 if label in ("baseline", "restored") else 1
                output = (run.stdout + run.stderr).decode("utf-8", errors="replace")
                if suite == "vm":
                    counts = {key: int(value) for key, value in re.findall(r"^# (tests|pass|fail) (\d+)$", output, re.M)}
                    failures = {"baseline": 0, "omit-stagger": 7, "freeze-stagger-reference": 4, "restored": 0}[label]
                    meaningful = counts == {"tests": 9, "pass": 9-failures, "fail": failures}
                    if failures:
                        meaningful = meaningful and "ERR_ASSERTION" in output and "grid-system" in output and "stagger" in output
                else:
                    counts = {"tests": 3} if re.search(r"Ran 3 tests? in", output) else {}
                    meaningful = bool(counts) and "ERROR:" not in output
                    if expected:
                        meaningful = meaningful and "FAIL:" in output and "AssertionError" in output
                results.append({"variant": label, "suite": suite, "exitCode": run.returncode,
                    "expectedExitCode": expected, "sourceSha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                    "log": str(log.resolve()), "counts": counts, "assertionOutcome": meaningful,
                    "passed": run.returncode == expected and meaningful})
    receipt = {"schema": "geometry-grid-inspector-mutations/1", "productSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "worktreeDirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)), "results": results}
    (args.out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
