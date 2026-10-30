"""Named mutation: reusing a colliding source id must fail the fresh-id test."""
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "geometry-web" / "definition-import.js"
TEST = ROOT / "tests" / "test_definition_import.js"
NEEDLE = "return candidate; /* DI-FRESH-ID */"
MUTANT = "return sourceId; /* DI-FRESH-ID */"


def run(source):
    env = os.environ.copy()
    env["GEOMETRY_DEFINITION_IMPORT_SOURCE"] = str(source)
    return subprocess.run(["node", "--test", str(TEST)], env=env, capture_output=True, text=True)


def main():
    text = SOURCE.read_text(encoding="utf-8")
    count = text.count(NEEDLE)
    if count != 1:
        raise SystemExit("needle count %s" % count)
    baseline = run(SOURCE)
    if baseline.returncode != 0:
        raise SystemExit("baseline failed\n" + baseline.stdout + baseline.stderr)
    temporary = Path(tempfile.mkdtemp(prefix="di-mutant-"))
    mutant = temporary / "definition-import.js"
    mutant.write_text(text.replace(NEEDLE, MUTANT, 1), encoding="utf-8")
    mutated = run(mutant)
    output = mutated.stdout + mutated.stderr
    # Node's default reporter is spec, so a red run names the test and exits
    # nonzero. It does not print the TAP token "not ok".
    if mutated.returncode == 0 or "撤掉實作：撞號仍沿用來源號碼" not in output or "notStrictEqual" not in output:
        raise SystemExit("mutant did not turn red\n" + output)
    restored = run(SOURCE)
    if restored.returncode != 0 or SOURCE.read_text(encoding="utf-8") != text:
        raise SystemExit("restore failed\n" + restored.stdout + restored.stderr)
    print("baseline 0")
    print("mutant %s" % mutated.returncode)
    print("restore 0")


if __name__ == "__main__":
    main()
