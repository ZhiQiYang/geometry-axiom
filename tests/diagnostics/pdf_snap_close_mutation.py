"""Prove PDF close-current-point withdrawals with the complete original suite.

Only TEMP copies of the product and its unmodified test are executed. A timeout,
crash, skipped test, wrong assertion or incomplete TAP is never a mutation kill.
Every named withdrawal must independently produce baseline/kill/restored 0/1/0.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("geometry-web/room-outline.js")
TEST = Path("tests/test_room_outline.js")
TEST_COUNT = 15
TEST_NAME = "manual PDF snap keeps original path endpoints, CTM and viewport; no text, curves, dashed or clipped paths"
KILLER = "P432_CLOSE_PATH_CONTINUATION"
TIMEOUT_SECONDS = 120
CASES = (
    {
        "name": "P432_DROP_CLOSE_CURRENT_POINT",
        "needle": "            finish(true);\n            if(start)pts.push(start);",
        "replacement": "            finish(true);",
    },
    {
        "name": "P432_WRONG_CLOSE_CURRENT_POINT",
        "needle": "            const start=pts[0];\n            if(start)pts.push(start);\n            finish(true);\n            if(start)pts.push(start);",
        "replacement": "            const start=pts[0],beforeClose=pts.at(-1);\n            if(start)pts.push(start);\n            finish(true);\n            if(start)pts.push(beforeClose);",
    },
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def judged(output: str, returncode: int | None, expected: int) -> bool:
    if returncode != expected or "Bail out!" in output:
        return False
    records = list(re.finditer(r"^(ok|not ok) (\d+) - ([^\r\n]+)\r?$", output, re.MULTILINE))
    if len(records) != TEST_COUNT or [int(m[2]) for m in records] != list(range(1, TEST_COUNT + 1)):
        return False
    if len({m[3] for m in records}) != TEST_COUNT or sum(m[3] == TEST_NAME for m in records) != 1:
        return False
    if re.findall(r"^1\.\.(\d+)\r?$", output, re.MULTILINE) != [str(TEST_COUNT)]:
        return False
    counts = {"tests": TEST_COUNT, "suites": 0, "pass": TEST_COUNT - expected,
              "fail": expected, "cancelled": 0, "skipped": 0, "todo": 0}
    if any(re.findall(r"^# " + key + r" (\d+)\r?$", output, re.MULTILINE) != [str(value)]
           for key, value in counts.items()):
        return False
    failed = [i for i, match in enumerate(records) if match[1] == "not ok"]
    if expected == 0:
        return not failed
    if len(failed) != 1 or records[failed[0]][3] != TEST_NAME:
        return False
    index = failed[0]
    diagnostic = output[records[index].end():records[index + 1].start() if index + 1 < len(records) else len(output)]
    fields = {"failureType": "testCodeFailure", "code": "ERR_ASSERTION",
              "name": "AssertionError", "operator": "deepStrictEqual"}
    if any(re.findall(r"^  " + key + r": '([^']*)'\r?$", diagnostic, re.MULTILINE) != [value]
           for key, value in fields.items()):
        return False
    return len(re.findall(r"^  error: \|-\r?\n    " + KILLER + r"\r?\n", diagnostic, re.MULTILINE)) == 1


def mutated(original: bytes, case: dict) -> bytes:
    # Preserve every byte outside the unique anchor, including checkout EOLs.
    needle = case["needle"].encode("utf-8")
    candidates = set((needle, needle.replace(b"\n", b"\r\n")))
    if sum(original.count(item) for item in candidates) != 1:
        raise ValueError(case["name"] + ": mutation anchor is not unique")
    found = next(item for item in candidates if original.count(item) == 1)
    replacement = case["replacement"].encode("utf-8")
    if b"\r\n" in found:
        replacement = replacement.replace(b"\n", b"\r\n")
    return original.replace(found, replacement, 1)


def run_once(root: Path, out: Path, name: str, phase: str, data: bytes, expected: int) -> dict:
    (root / SOURCE).write_bytes(data)
    command = ["node", "--test", "--test-reporter=tap", str(root / TEST)]
    started = time.monotonic()
    error = None
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, timeout=TIMEOUT_SECONDS, check=False)
        stdout, stderr, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, code = exc.stdout or b"", exc.stderr or b"", None
        error = "timeout"
    except OSError as exc:
        stdout, stderr, code = b"", str(exc).encode("utf-8"), None
        error = "execution-error"
    prefix = name + "." + phase
    (out / (prefix + ".tap")).write_bytes(stdout)
    (out / (prefix + ".stderr")).write_bytes(stderr)
    passed = error is None and not stderr and judged(stdout.decode("utf-8", errors="replace"), code, expected)
    record = {"name": name, "phase": phase, "exit": code, "expected": expected,
              "passed": passed, "error": error, "elapsed_seconds": time.monotonic() - started,
              "source_bytes": len(data), "source_sha256": sha(data), "command": command,
              "stdout": prefix + ".tap", "stdout_sha256": sha(stdout),
              "stderr": prefix + ".stderr", "stderr_sha256": sha(stderr),
              "killer": KILLER if expected == 1 else None}
    (out / (prefix + ".json")).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{name} {phase}: exit={code} expected={expected} passed={passed}")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="new directory outside the repository for raw TAP and receipts")
    args = parser.parse_args()
    if args.out:
        out = args.out.resolve()
        if out == ROOT or ROOT in out.parents or out.exists():
            parser.error("--out must be a new directory outside the repository")
        out.mkdir(parents=True)
    else:
        out = Path(tempfile.mkdtemp(prefix="geometry-pdf-snap-close-mutations-"))
    original, test = (ROOT / SOURCE).read_bytes(), (ROOT / TEST).read_bytes()
    try:
        head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                              text=True, timeout=10, check=True).stdout.strip()
        if not re.fullmatch(r"[0-9a-f]{40}", head):
            raise ValueError("git HEAD is not a complete SHA")
        variants = [(case["name"], mutated(original, case)) for case in CASES]
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        (out / "setup-error.txt").write_text(str(exc) + "\n", encoding="utf-8")
        print("blocked:", exc)
        print("logs", out)
        return 2
    receipt = {"schema": "geometry-pdf-snap-close-mutations/1", "git_head": head,
               "source": SOURCE.as_posix(), "source_bytes": len(original), "source_sha256": sha(original),
               "test": TEST.as_posix(), "test_bytes": len(test), "test_sha256": sha(test),
               "tool_sha256": sha(Path(__file__).read_bytes()), "test_count": TEST_COUNT,
               "timeout_seconds": TIMEOUT_SECONDS, "results": [], "passed": False}
    with tempfile.TemporaryDirectory(prefix="geometry-pdf-snap-close-src-") as directory:
        root = Path(directory)
        (root / SOURCE.parent).mkdir(parents=True)
        (root / TEST.parent).mkdir(parents=True)
        (root / TEST).write_bytes(test)
        for name, mutant in variants:
            for phase, data, expected in (("baseline", original, 0), ("mutant", mutant, 1), ("restored", original, 0)):
                result = run_once(root, out, name, phase, data, expected)
                receipt["results"].append(result)
                (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
                if phase == "baseline" and not result["passed"]:
                    print("blocked: baseline is not green")
                    print("logs", out)
                    return 2
    receipt["workspace_unchanged"] = (ROOT / SOURCE).read_bytes() == original and (ROOT / TEST).read_bytes() == test
    receipt["passed"] = receipt["workspace_unchanged"] and all(row["passed"] for row in receipt["results"])
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("logs", out)
    print("PASSED" if receipt["passed"] else "BLOCKED")
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
