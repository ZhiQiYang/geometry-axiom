"""Named red/green probe: a stale room-candidate row must stay unselectable.

Only a TEMP copy of room-candidate-draft.js is mutated. The product tree is read.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "geometry-web" / "room-candidate-draft.js"
TARGET = 'if (!report.fresh) fail("過期草稿不可選取、預覽或接受。");'
MUTANT = "if (!report.fresh) return;"


NAME = "撤掉實作：過期列不得接受"


def tap_marks(output):
    ok = not_ok = False
    for line in output.splitlines():
        if NAME not in line:
            continue
        if line.startswith("not ok"):
            not_ok = True
        elif line.startswith("ok "):
            ok = True
    return ok, not_ok


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
            completed = subprocess.run(["node", "--test", "--test-reporter=tap", "tests/test_room_candidate_draft.js"],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
            output = completed.stdout + completed.stderr
            (out / (label + ".log")).write_text(output, encoding="utf-8")
            ok, not_ok = tap_marks(output)
            named_ok = ok and not not_ok if expected == 0 else not_ok
            results.append({"variant": label, "exit": completed.returncode, "expected": expected,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "ok": ok, "not_ok": not_ok,
                "passed": completed.returncode == expected and named_ok})
    print("\n".join(
        f"{item['variant']} exit={item['exit']} expected={item['expected']} ok={item['ok']} not_ok={item['not_ok']}"
        for item in results))
    print("logs", out)
    return 0 if all(item["passed"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
