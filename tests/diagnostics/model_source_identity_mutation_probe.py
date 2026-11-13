"""Copy the identity ledger and require each named K3-44 removal to go red.

The workspace source is never modified. Node's spec reporter prints the named
failure with operator strictEqual. M-13(e) is not executed.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "geometry-web" / "identity-ledger.js"
TEST = ROOT / "tests" / "test_model_source_identity.js"
CASES = (
    {
        "needle": 'item && item.status === "continuous" && item.incarnation && !item.uncovered) /* 只預填延續 */',
        "mutant": 'item && item.id != null) /* 只預填延續 */',
        "name": "撤掉實作：同編號就預填",
    },
    {
        "needle": 'if (reviewed[i].status !== live[i].status || reviewed[i].incarnation !== live[i].incarnation || reviewed[i].id !== live[i].id) return {ok: false, code: "STALE"};',
        "mutant": 'if (false) return {ok: false, code: "STALE"};',
        "name": "撤掉實作：確認不重比",
    },
    {
        "needle": 'pinsEqual !== true) return []; /* 指紋變不預填邊 */',
        "mutant": 'false) return []; /* 指紋變不預填邊 */',
        "name": "撤掉實作：定義指紋變仍預填邊",
    },
    {
        "needle": "/* 去身分基準 */",
        "mutant": 'return String(scene == null ? "" : scene); /* 含記號基準 */',
        "name": "撤掉實作：基準保留記號",
    },
)


def killed(combined: str, name: str) -> bool:
    section = combined.split("failing tests:", 1)[-1]
    start = section.find(name)
    if start < 0:
        return False
    nxt = section.find("\ntest at ", start + 1)
    chunk = section[start:] if nxt < 0 else section[start:nxt]
    return "operator: 'strictEqual'" in chunk


def run(copy: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["MODEL_SOURCE_IDENTITY_MODULE"] = str(copy)
    return subprocess.run(
        ["node", "--test", str(TEST)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    text = SOURCE.read_text(encoding="utf-8")
    for case in CASES:
        if text.count(case["needle"]) != 1 or (case["mutant"] and case["mutant"] in text):
            print("needle count", case["name"], text.count(case["needle"]))
            return 2
    with tempfile.TemporaryDirectory(prefix="geometry-model-source-identity-mutation-") as directory:
        copy = Path(directory) / "identity-ledger.js"
        copy.write_text(text, encoding="utf-8", newline="\n")
        baseline = run(copy)
        if baseline.returncode != 0:
            print(baseline.stdout)
            print(baseline.stderr, file=sys.stderr)
            print("baseline", baseline.returncode)
            return 1
        print("baseline", baseline.returncode)
        for case in CASES:
            copy.write_text(text.replace(case["needle"], case["mutant"], 1), encoding="utf-8", newline="\n")
            mutant = run(copy)
            combined = mutant.stdout + mutant.stderr
            if mutant.returncode == 0 or not killed(combined, case["name"]):
                print(mutant.stdout)
                print(mutant.stderr, file=sys.stderr)
                print("mutant", case["name"], mutant.returncode)
                return 1
            print("killed", case["name"])
        copy.write_text(text, encoding="utf-8", newline="\n")
        restored = run(copy)
        if restored.returncode != 0:
            print(restored.stdout)
            print(restored.stderr, file=sys.stderr)
            print("restore", restored.returncode)
            return 1
        print("restore", restored.returncode)
    print("PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
