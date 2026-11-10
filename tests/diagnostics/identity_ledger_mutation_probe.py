"""Copy the identity-ledger mirror, keep the old mark, and require the named test to go red.

The workspace source is never modified. Node's spec reporter prints the test
name and notStrictEqual; this probe does not look for TAP.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "geometry-web" / "identity-ledger.js"
TEST = ROOT / "tests" / "test_identity_ledger.js"
NEEDLE = "return allocate(); /* 不得沿用舊記號 */"
MUTANT = "return beforeMark; /* 沿用舊記號 */"
NAME = "撤掉實作：沿用舊記號"


def run(copy: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["IDENTITY_LEDGER_MODULE"] = str(copy)
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
    if text.count(NEEDLE) != 1 or MUTANT in text:
        print("needle count", text.count(NEEDLE))
        return 2
    with tempfile.TemporaryDirectory(prefix="geometry-identity-ledger-mutation-") as directory:
        copy = Path(directory) / "identity-ledger.js"
        copy.write_text(text, encoding="utf-8", newline="\n")
        baseline = run(copy)
        print(baseline.stdout)
        print(baseline.stderr, file=sys.stderr)
        if baseline.returncode != 0:
            print("baseline", baseline.returncode)
            return 1
        copy.write_text(text.replace(NEEDLE, MUTANT, 1), encoding="utf-8", newline="\n")
        mutant = run(copy)
        print(mutant.stdout)
        print(mutant.stderr, file=sys.stderr)
        combined = mutant.stdout + mutant.stderr
        if mutant.returncode == 0 or NAME not in combined or "notStrictEqual" not in combined:
            print("mutant", mutant.returncode)
            return 1
        copy.write_text(text, encoding="utf-8", newline="\n")
        restored = run(copy)
        print(restored.stdout)
        print(restored.stderr, file=sys.stderr)
        if restored.returncode != 0:
            print("restore", restored.returncode)
            return 1
    print("PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
