"""Named display-only withdrawal; does not alter any test or native definition.

python tests/diagnostics/d02_length_overlay_withdrawal.py --out /tmp/d02-withdrawal
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "geometry-web/app.js"
COMMAND = ["node", "--test", "--test-reporter=spec", "tests/test_face_length_overlay.js"]
NAME = "D02_WITHDRAW_OBSTACLE_AVOIDANCE"
KILL = "D02_TYPED_CLEAR_FIRST_LESSON: clear of instruction/cursor overlay"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    before = PRODUCT.read_bytes()
    start = b"  /* The typed value is a readonly mirror, not another source of geometry."
    end = b'  inp.style.top = position.top + "px";'
    if before.count(start) != 1 or before.count(end) != 1:
        raise RuntimeError("withdrawal anchor must match the real implementation exactly once")
    a, b = before.index(start), before.index(end) + len(end)
    original = (b'  inp.style.left = (c[0] * fe.zoom + fe.panX + 12) + "px";\n'
                b'  inp.style.top = (c[1] * fe.zoom + fe.panY - 30) + "px";')
    receipt = {"name": NAME, "command": COMMAND, "killAssertion": KILL,
               "sourceBeforeSha256": hashlib.sha256(before).hexdigest(),
               "testSha256": hashlib.sha256((ROOT / COMMAND[-1]).read_bytes()).hexdigest(),
               "runs": []}

    def run(label):
        began = time.monotonic()
        result = subprocess.run(COMMAND, cwd=ROOT, capture_output=True, timeout=120)
        (args.out / (label + ".stdout")).write_bytes(result.stdout)
        (args.out / (label + ".stderr")).write_bytes(result.stderr)
        row = {"label": label, "exit": result.returncode,
               "seconds": time.monotonic() - began,
               "sourceSha256": hashlib.sha256(PRODUCT.read_bytes()).hexdigest()}
        receipt["runs"].append(row)
        return result

    try:
        green = run("green")
        if green.returncode != 0:
            raise AssertionError("unmodified implementation must be green")
        PRODUCT.write_bytes(before[:a] + original + before[b:])
        mutant = run(NAME)
        if mutant.returncode != 1 or KILL.encode() not in mutant.stdout + mutant.stderr:
            raise AssertionError("withdrawal must fail the designated visual-overlap assertion")
    finally:
        PRODUCT.write_bytes(before)
        restored = run("restored")
        receipt["sourceAfterSha256"] = hashlib.sha256(PRODUCT.read_bytes()).hexdigest()
        receipt["exitSequence"] = [row["exit"] for row in receipt["runs"]]
        receipt["verified"] = (receipt["exitSequence"] == [0, 1, 0]
                               and receipt["sourceBeforeSha256"] == receipt["sourceAfterSha256"])
        (args.out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if restored.returncode != 0 or not receipt["verified"]:
        raise AssertionError("required green/withdrawal/restored sequence is 0/1/0")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
