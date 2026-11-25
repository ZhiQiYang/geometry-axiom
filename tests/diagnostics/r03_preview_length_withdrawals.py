"""Physical CSS/markup withdrawals; Node contracts and Chromium stay separate.

Source: python3 -B tests/diagnostics/r03_preview_length_withdrawals.py --out /tmp/r03-length-source
Browser: GEOMETRY_TEST_URL=http://localhost:PORT/ GEOMETRY_CHROME=/path/to/chrome \
  python3 -B tests/diagnostics/r03_preview_length_withdrawals.py --browser --out /tmp/r03-length-chrome

Browser mode needs the caller's isolated current-build service and Chromium.
Every cdp_test invocation owns its own browser process. This script never
starts, stops or resets a user's service. It restores the exact CSS bytes in
finally, and saves stdout/stderr for each actual baseline/withdrawal/restore.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CSS = ROOT / "geometry-web/framing-template-workspace.css"
MARKUP = ROOT / "geometry-web/framing-template-workspace.js"
RULE = (b".ft-workspace .ft-results [data-ft-length]"
        b"{white-space:nowrap;overflow-wrap:normal;word-break:normal}\n")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("output directory must be new")
    if args.browser and not os.environ.get("GEOMETRY_TEST_URL"):
        raise ValueError("browser mode requires GEOMETRY_TEST_URL for an isolated current-build service")
    args.out.mkdir(parents=True)
    original = {CSS: CSS.read_bytes(), MARKUP: MARKUP.read_bytes()}
    if original[CSS].count(RULE) != 1:
        raise AssertionError("R03_LENGTH_WITHDRAWAL_ANCHOR: expected exactly one reviewed CSS rule")
    cell = b'<td data-ft-length>${m.length}</td>'
    if original[MARKUP].count(cell) != 1:
        raise AssertionError("R03_LENGTH_MARKUP_ANCHOR: expected exactly one reviewed numeric cell")
    variants = {
        "R03_LENGTH_REMOVE_NUMERIC_RULE": ({**original, CSS: original[CSS].replace(RULE, b"")}, "R03_PREVIEW_LENGTH_POLICY"),
        "R03_LENGTH_STYLE_WRONG_FIELD": ({**original, CSS: original[CSS].replace(RULE, RULE.replace(b"data-ft-length", b"data-ft-width"))}, "R03_PREVIEW_LENGTH_POLICY"),
        "R03_LENGTH_DROP_CELL_MARKER": ({**original, MARKUP: original[MARKUP].replace(cell, b'<td>${m.length}</td>')}, "R2054_LENGTH_SEMANTIC_CELL"),
    }
    env = os.environ.copy()
    if args.browser:
        env["GEOMETRY_CANVAS_MODULE_ONLY"] = "1"
        env["GEOMETRY_CANVAS_MODULE"] = "P2054"
        command = ["node", "geometry-web/cdp_test.js"]
    else:
        command = ["node", "--test", "tests/test_r03_preview_length.js"]
    records = []
    try:
        for name, (withdrawn, marker) in variants.items():
            phases = []
            for phase, sources in (("baseline", original), ("withdrawn", withdrawn), ("restored", original)):
                for target, raw in sources.items():
                    target.write_bytes(raw)
                    if target.read_bytes() != raw:
                        raise AssertionError("R03_LENGTH_SOURCE_WRITE")
                completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                           timeout=2100 if args.browser else 60)
                stem = args.out / (name + "." + phase)
                stem.with_suffix(stem.suffix + ".stdout.log").write_bytes(completed.stdout)
                stem.with_suffix(stem.suffix + ".stderr.log").write_bytes(completed.stderr)
                output = completed.stdout.decode("utf-8", "replace")
                errors = completed.stderr.decode("utf-8", "replace")
                row = {"phase": phase, "exit": completed.returncode, "sources_sha256": {str(k.relative_to(ROOT)): sha(v) for k,v in sources.items()},
                       "stdout_sha256": sha(completed.stdout), "stderr_sha256": sha(completed.stderr)}
                if args.browser:
                    lines = [line[11:] for line in output.splitlines() if line.startswith("CDP_RESULT ")]
                    if len(lines) != 1:
                        raise AssertionError(name + " " + phase + " lacks one complete CDP_RESULT")
                    result = json.loads(lines[0])
                    if not (result["completed"] is True and result["sectionOrder"] == ["P2054"] and
                            result["unexpectedBrowserExceptions"] == 0 and result["uncaughtBrowserExceptions"] == 0):
                        raise AssertionError(name + " " + phase + " is not a clean P2054 execution")
                    if phase == "withdrawn":
                        if "P2054 R03_PREVIEW_LENGTH_SINGLE_LINE v2 1400 ✗" not in output:
                            raise AssertionError(name + " wrong browser failure; a crash is not a kill")
                    elif result["sections"] != {"P2054": 15} or result["failedAssertions"] != 0:
                        raise AssertionError(name + " " + phase + " is not all 15 planned assertions")
                    row["cdp_result"] = result
                elif phase == "withdrawn" and not ("AssertionError" in output+errors and marker in output+errors):
                    raise AssertionError(name + " wrong Node failure; a crash is not a kill")
                phases.append(row)
            if [row["exit"] for row in phases] != [0, 1, 0]:
                raise AssertionError(name + " expected 0/1/0, got " + repr([row["exit"] for row in phases]))
            records.append({"name": name, "phases": phases})
    finally:
        for target, raw in original.items():
            target.write_bytes(raw)
            if target.read_bytes() != raw:
                raise AssertionError("R03_LENGTH_RESTORE_EXACT_BYTES")
    report = {"schema": "r03-preview-length-withdrawals/2", "mode": "chromium-layout" if args.browser else "node-markup-and-source-policy",
              "base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "command": command, "sources_restored_sha256": {str(k.relative_to(ROOT)): sha(k.read_bytes()) for k in original}, "withdrawals": records,
              "browserExecuted": args.browser}
    (args.out / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
