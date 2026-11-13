"""Verify the archived preproduction scanner evidence without executing tests."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys


SOURCE = "99455b9f73c4175c1154f7e7be514204019930b8"
BEFORE = "70ccab62d4fb3d3aba4dbac919f19ad3e4f8a7c8"
SKIP = "test_symlink_escape_is_rejected"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def basename(path):
    return path.replace("\\", "/").rsplit("/", 1)[-1]


def check_log(path, row):
    raw = path.read_bytes()
    require(sha(raw) == row["logSha256"], f"log hash: {path.name}")
    text = raw.decode("utf-8").replace("\r\n", "\n")
    counts = re.findall(r"^Ran (\d+) tests? in ", text, re.M)
    require(counts == [str(row["testsRun"])], f"test count: {path.name}")
    for field, pattern in (
        ("failedCases", r"^FAIL: ([^ ]+)"),
        ("errorCases", r"^ERROR: ([^ ]+)"),
        ("skippedCases", r"^(test_[^ ]+) .* \.\.\. skipped "),
    ):
        require(re.findall(pattern, text, re.M) == row[field], f"{field}: {path.name}")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest = read_json(root / "artifact-manifest.json")
    require(manifest["sourceCommit"] == SOURCE, "manifest source")
    rows = manifest["files"]
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*")
              if p.is_file() and p.name != "artifact-manifest.json"
              and "__pycache__" not in p.parts}
    require(set(rows) == actual, "package inventory differs")
    for name, row in rows.items():
        raw = (root / name).read_bytes()
        require(len(raw) == row["bytes"] and sha(raw) == row["sha256"], f"artifact bytes: {name}")

    delivery = read_json(root / "final-delivery-205.json")
    mutation_dir = root / "architecture-comprehension-mutation-205"
    mutation = read_json(mutation_dir / "mutation-results.json")
    proof_dir = root / "architecture-comprehension-root-proof-portable"
    proof = read_json(proof_dir / "receipt.json")
    runners = root / "runners"
    require(delivery["head"] == SOURCE and delivery["workingTreeStatus"] == [], "delivery source/state")
    require(mutation["head"] == BEFORE, "historical precommit head")
    require(sha((mutation_dir / "mutation-results.json").read_bytes()) == delivery["receiptSha256"], "delivery receipt binding")
    require(all(delivery["inputsUnchanged"].values()) and all(mutation["inputsUnchanged"].values()), "source unchanged receipts")
    require(delivery["temporaryCopiesDeleted"] and mutation["temporaryCopiesDeleted"], "temporary copy cleanup")
    require(mutation["exit"] == 0, "mutation runner exit")
    require(delivery["testsRun"] == 205 and delivery["skips"] == [SKIP], "delivery baseline counts")
    for name, row in delivery["files"].items():
        require(row["commitBlobMatches"], f"delivery commit binding: {name}")
        require(mutation["inputsBefore"][name] == row["rawSha256"], f"mutation input binding: {name}")
        blob = subprocess.check_output(["git", "show", SOURCE + ":" + name], cwd=args.repo)
        require(sha(blob.replace(b"\r\n", b"\n")) == row["lfSha256"], f"source Git blob: {name}")

    baseline = mutation["baseline"]
    require(baseline["exit"] == 0 and baseline["testsRun"] == 205
            and baseline["failedCases"] == [] and baseline["errorCases"] == []
            and baseline["skippedCases"] == [SKIP], "original baseline outcome")
    require("OK (skipped=1)" in check_log(mutation_dir / "baseline.log", baseline), "baseline success marker")
    mutants = mutation["mutants"]
    require(len(mutants) == len({m["control"] for m in mutants}) == 43, "43 unique mutation controls")
    require(sum(len(m["failedCases"]) for m in mutants) == 99, "99 actual expected failures")
    require(sum(len(m["expectedFailedCases"]) for m in mutants) == 99, "99 declared expected failures")
    require(delivery["focusedNegativeControls"] == 43 and delivery["expectedTestFailures"] == 99
            and delivery["actualTestFailures"] == 99 and delivery["mutationErrors"] == 0, "delivery mutation counts")

    runner = runners / "mutate_architecture_comprehension_v9.py.txt"
    require(sha(runner.read_bytes()) == mutation["runnerSha256"], "v9 runner hash")
    require(len(mutation["baseRunners"]) == 4, "four base runners")
    for row in mutation["baseRunners"]:
        require(sha((runners / basename(row["path"])).read_bytes()) == row["sha256"], "base runner hash")
    loader = importlib.machinery.SourceFileLoader("geo261_archived_mutation_v9", str(runner))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    require(set(module.runner.CONTROLS) == {m["control"] for m in mutants}, "runner control inventory")
    source = subprocess.check_output(["git", "show", SOURCE + ":tests/architecture_contract.py"], cwd=args.repo).decode("utf-8").replace("\r\n", "\n")
    for row in mutants:
        control = row["control"]
        require(row["exit"] == 1 and row["testsRun"] == len(row["expectedFailedCases"])
                and row["failedCases"] == row["expectedFailedCases"]
                and not row["errorCases"] and not row["skippedCases"], f"expected red only: {control}")
        require(module.runner.CONTROLS[control] == row["expectedFailedCases"], f"runner case list: {control}")
        check_log(mutation_dir / (control + ".log"), row)
        changed = module.mutate(source, control)
        require(sha(changed.encode("utf-8")) == row["mutantSha256"], f"regenerated mutant: {control}")
        diff = "".join(difflib.unified_diff(source.splitlines(True), changed.splitlines(True),
                       fromfile="tests/architecture_contract.py", tofile="TEMP/architecture_contract.py"))
        archived_diff = (mutation_dir / (control + ".diff")).read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        require(diff == archived_diff, f"regenerated diff: {control}")

    require(sha((runners / "verify_architecture_comprehension_root.py").read_bytes()) == proof["runnerSha256"], "independent runner hash")
    require(proof["temporaryRemoved"], "independent temporary cleanup")
    for label, commit in (("before", BEFORE), ("after", SOURCE)):
        version = proof["versions"][label]
        require(version["sha"] == commit, f"independent {label} commit")
        blob = subprocess.check_output(["git", "show", commit + ":tests/architecture_contract.py"], cwd=args.repo)
        require(sha(blob) == version["scannerSha256"], f"independent {label} scanner")
        require(set(version["results"]) == {"unpack", "indexed"}, "independent case inventory")
        for result in version["results"].values():
            if label == "before":
                require(result["ok"] and not result["diagnostics"], "original false green")
            else:
                require(not result["ok"] and any(d["code"] == "CORE_PATH_INJECTION" and d["path"] == "src/k/core.py" for d in result["diagnostics"]), "fixed explicit rejection")
    frozen = proof["frozenSuite"]
    require(frozen["source"] == SOURCE and frozen["exit"] == 0
            and frozen["testsRun"] == 205 and frozen["skips"] == 1, "independent baseline counts")
    for name, digest in frozen["inputs"].items():
        require(digest == delivery["files"]["tests/" + name]["lfSha256"], f"frozen input binding: {name}")
    independent_row = dict(frozen, failedCases=[], errorCases=[], skippedCases=[SKIP])
    require("OK (skipped=1)" in check_log(proof_dir / "frozen-205.log", independent_row), "independent baseline success marker")
    print(json.dumps({"ok": True, "source": SOURCE, "filesVerified": len(rows),
                      "baseline": {"run": 205, "passed": 204, "skipped": 1},
                      "mutationControls": 43, "expectedFailures": 99, "errors": 0,
                      "mutantsRegeneratedInMemory": 43,
                      "scope": "archived preproduction fixture evidence; no product execution"}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, KeyError, ValueError, OSError, subprocess.CalledProcessError) as error:
        print("Evidence verification failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
