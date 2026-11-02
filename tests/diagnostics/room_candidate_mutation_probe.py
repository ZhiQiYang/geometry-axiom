"""Named red/green probe: a stale room-candidate row must stay unselectable.

Only a TEMP copy of room-candidate-draft.js is mutated. The product tree is read.
"""
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "geometry-web" / "room-candidate-draft.js"
TARGET = 'if (!report.fresh) fail("過期草稿不可選取、預覽或接受。");'
MUTANT = "if (!report.fresh) return;"


NAME = "撤掉實作：過期列不得接受"
TEST_COUNT = 7


def judge(output, returncode, expected):
    """Require the complete suite and exactly the intended throws assertion.

    A named test can also fail before reaching that assertion (TypeError,
    fixture failure, cancellation). Its TAP name and exit code are not proof.
    """
    if returncode != expected or "Bail out!" in output:
        return False
    records = list(re.finditer(r"^(ok|not ok) (\d+) - (.+)$", output, re.MULTILINE))
    if len(records) != TEST_COUNT or [int(m[2]) for m in records] != list(range(1, TEST_COUNT + 1)):
        return False
    if len({m[3] for m in records}) != TEST_COUNT or sum(m[3] == NAME for m in records) != 1:
        return False
    if re.findall(r"^1\.\.(\d+)$", output, re.MULTILINE) != [str(TEST_COUNT)]:
        return False
    counts = {"tests": TEST_COUNT, "suites": 0, "pass": TEST_COUNT - expected,
              "fail": expected, "cancelled": 0, "skipped": 0, "todo": 0}
    if any(re.findall(r"^# " + key + r" (\d+)$", output, re.MULTILINE) != [str(value)]
           for key, value in counts.items()):
        return False
    failed = [i for i, match in enumerate(records) if match[1] == "not ok"]
    if expected == 0:
        return not failed
    if len(failed) != 1 or records[failed[0]][3] != NAME:
        return False
    index = failed[0]
    diagnostic = output[records[index].end():records[index + 1].start() if index + 1 < len(records) else len(output)]
    fields = {"failureType": "testCodeFailure", "error": "Missing expected exception.",
              "code": "ERR_ASSERTION", "name": "AssertionError", "operator": "throws"}
    return all(re.findall(r"^  " + key + r": '([^']*)'$", diagnostic, re.MULTILINE) == [value]
               for key, value in fields.items())


def main():
    original = SOURCE.read_text(encoding="utf-8")
    if original.count(TARGET) != 1:
        print("mutation target is not unique")
        return 2
    out = Path(tempfile.mkdtemp(prefix="geometry-room-candidate-mutation-"))
    mutant = original.replace(TARGET, MUTANT, 1)
    results = []
    with tempfile.TemporaryDirectory(prefix="geometry-room-candidate-src-") as tmp:
        for label, text, expected in (("baseline", original, 0), ("mutant", mutant, 1), ("restored", original, 0)):
            path = Path(tmp) / (label + ".js")
            path.write_text(text, encoding="utf-8")
            env = {**os.environ, "GEOMETRY_ROOM_CANDIDATE_SOURCE": str(path)}
            try:
                completed = subprocess.run(["node", "--test", "--test-reporter=tap", "tests/test_room_candidate_draft.js"],
                    cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
            except (OSError, subprocess.TimeoutExpired) as error:
                (out / (label + ".log")).write_text(str(error), encoding="utf-8")
                print(label, "execution error:", error)
                print("logs", out)
                return 2
            output = completed.stdout + completed.stderr
            (out / (label + ".log")).write_text(output, encoding="utf-8")
            results.append({"variant": label, "exit": completed.returncode, "expected": expected,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "passed": not completed.stderr and judge(completed.stdout, completed.returncode, expected)})
    print("\n".join(
        f"{item['variant']} exit={item['exit']} expected={item['expected']} passed={item['passed']}"
        for item in results))
    print("logs", out)
    return 0 if all(item["passed"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
