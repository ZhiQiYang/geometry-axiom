"""Named mutations for definition-import/1; each must turn its unit test red.

DI-FRESH-ID: reusing a colliding source id must fail the fresh-id test.
DI-PREVIEW-CURRENT: a preview that stays confirmable after an input edit
must fail the preview-gate test (#359 review B1/B2).
"""
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "geometry-web" / "definition-import.js"
TEST = ROOT / "tests" / "test_definition_import.js"
MUTATIONS = [
    ("DI-FRESH-ID",
     "return candidate; /* DI-FRESH-ID */",
     "return sourceId; /* DI-FRESH-ID */",
     "撤掉實作：撞號仍沿用來源號碼",
     "notStrictEqual"),
    ("DI-PREVIEW-CURRENT",
     "return previewed === generation; /* DI-PREVIEW-CURRENT */",
     "return previewed >= 0; /* DI-PREVIEW-CURRENT */",
     "撤掉實作：輸入變更後舊預覽仍可確認",
     "strictly equal"),
]


def run(source):
    env = os.environ.copy()
    env["GEOMETRY_DEFINITION_IMPORT_SOURCE"] = str(source)
    return subprocess.run(["node", "--test", str(TEST)], env=env, capture_output=True, text=True)


def main():
    text = SOURCE.read_text(encoding="utf-8")
    for name, needle, _, _, _ in MUTATIONS:
        count = text.count(needle)
        if count != 1:
            raise SystemExit("%s needle count %s" % (name, count))
    baseline = run(SOURCE)
    if baseline.returncode != 0:
        raise SystemExit("baseline failed\n" + baseline.stdout + baseline.stderr)
    print("baseline 0")
    temporary = Path(tempfile.mkdtemp(prefix="di-mutant-"))
    for name, needle, replacement, test_name, marker in MUTATIONS:
        mutant = temporary / (name + "-definition-import.js")
        mutant.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
        mutated = run(mutant)
        output = mutated.stdout + mutated.stderr
        # Node's default reporter is spec, so a red run names the test and exits
        # nonzero. It does not print the TAP token "not ok".
        if mutated.returncode == 0 or test_name not in output or marker not in output:
            raise SystemExit("%s did not turn red\n%s" % (name, output))
        print("mutant %s %s" % (name, mutated.returncode))
    restored = run(SOURCE)
    if restored.returncode != 0 or SOURCE.read_text(encoding="utf-8") != text:
        raise SystemExit("restore failed\n" + restored.stdout + restored.stderr)
    print("restore 0")


if __name__ == "__main__":
    main()
