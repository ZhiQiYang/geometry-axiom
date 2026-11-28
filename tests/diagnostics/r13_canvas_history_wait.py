#!/usr/bin/env python3
"""Withdraw each P4313 history-completion wait in an isolated source copy.

This executes the real App handler and save guard through the Node scheduling
regression; it is not a Chromium receipt. No product or registry file is edited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "geometry-web/canvas_sections/P4313.js"
TEST = "tests/test_r13_reconstruction_ui.js"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out == ROOT or ROOT in out.parents or (out.exists() and any(out.iterdir())):
        parser.error("--out must be an empty directory outside the checkout")
    out.mkdir(parents=True, exist_ok=True)
    original = SOURCE.read_bytes()
    rows = []
    with tempfile.TemporaryDirectory(prefix="r13-history-wait-") as temp:
        for verb in ("undo", "redo"):
            name = "R13_CANVAS_" + verb.upper() + "_IDLE_WAIT_WITHDRAWN"
            assertion = "R13_CANVAS_" + verb.upper() + "_WAITS_FOR_HISTORY_IDLE"
            title = "R13 canvas " + verb + " waits for both App repaint stages before saving"
            anchor = ("await ctl('#face" + verb.title() + "Button');await waitForUI(`"
                      "ReferenceWorkspace.getEvidenceState().blocked===false&&").encode()
            if original.count(anchor) != 1:
                raise AssertionError("R13_CANVAS_WITHDRAWAL_UNIQUE_ANCHOR " + name)
            replacement = anchor.replace(b"ReferenceWorkspace.getEvidenceState().blocked===false&&", b"")
            withdrawn = Path(temp) / (name + ".js")
            withdrawn.write_bytes(original.replace(anchor, replacement, 1))
            phases = []
            for phase, selected in (("baseline", SOURCE), ("withdrawn", withdrawn), ("restored", SOURCE)):
                env = dict(os.environ, GEOMETRY_R13_CANVAS_SOURCE=str(selected))
                command = ["node", "--test", "--test-reporter=tap", "--test-name-pattern=^" + re.escape(title) + "$", TEST]
                result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=45)
                prefix = out / (name + "-" + phase)
                prefix.with_suffix(".stdout").write_bytes(result.stdout)
                prefix.with_suffix(".stderr").write_bytes(result.stderr)
                text = (result.stdout + result.stderr).decode("utf-8", "replace")
                counts = {key: int(value) for key, value in re.findall(r"^# (tests|pass|fail|cancelled|skipped|todo) (\d+)$", text, re.M)}
                red = phase == "withdrawn"
                expected = {"tests": 1, "pass": int(not red), "fail": int(red), "cancelled": 0, "skipped": 0, "todo": 0}
                ok = result.returncode == int(red) and counts == expected and (not red or ("ERR_ASSERTION" in text and assertion in text))
                row = {"phase": phase, "command": command, "exit": result.returncode, "counts": counts, "verified": ok,
                       "stdoutBytes": len(result.stdout), "stdoutSha256": hashlib.sha256(result.stdout).hexdigest(),
                       "stderrBytes": len(result.stderr), "stderrSha256": hashlib.sha256(result.stderr).hexdigest()}
                prefix.with_suffix(".json").write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                phases.append(row)
                if not ok:
                    raise AssertionError("R13_CANVAS_WITHDRAWAL_RESULT " + name + " " + phase)
            rows.append({"name": name, "assertion": assertion, "phases": phases})
            print(name + " " + "/".join(str(row["exit"]) for row in phases))
    if SOURCE.read_bytes() != original:
        raise AssertionError("R13_CANVAS_SOURCE_CHANGED_DURING_WITHDRAWALS")
    (out / "summary.json").write_text(json.dumps({"sourceSha256": hashlib.sha256(original).hexdigest(),
        "browser": False, "withdrawals": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
