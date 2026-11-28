#!/usr/bin/env python3
"""Bounded R11 T1 source withdrawals; no Chrome or CI receipt is claimed.

Each phase runs the real adapter from an isolated on-disk source copy. A kill
requires one exact named Node AssertionError, not a timeout or setup failure.
The restored phase verifies exact bytes and executes that same case again.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
DEFINITIONS = Path(__file__).with_suffix(".json")
PRODUCTS = ("geometry-web/app.js", "geometry-web/face-context-menu.js",
            "geometry-web/space-context-menu.js")
SUITES = ("tests/test_r11_face_keyboard.js", "tests/test_r11_space_clipboard.js")
PHASE_LIMIT_SECONDS = 20
TOTAL_LIMIT_SECONDS = 180


def digest(data):
    return hashlib.sha256(data).hexdigest()


def phase(root, suite, case, expected, deadline):
    command = ["node", "--test", "--test-reporter=tap", str(ROOT / suite)]
    env = os.environ.copy()
    # Do not inherit the standalone suite's optional in-memory mutation hook.
    for key in ("GEOMETRY_R11_SPACE_MUTANT", "GEOMETRY_R11_SPACE_CASE"):
        env.pop(key, None)
    exact = {"GEOMETRY_R11_T1_ROOT": str(root), "GEOMETRY_R11_T1_CASE": case}
    env.update(exact)
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise RuntimeError("T476_WITHDRAWAL_TOTAL_DEADLINE: not a kill")
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                timeout=min(PHASE_LIMIT_SECONDS, remaining))
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("T476_WITHDRAWAL_TIMEOUT: not a kill") from error
    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")
    row = {"command": command, "cwd": str(ROOT), "env": exact,
           "exit_code": result.returncode, "seconds": time.monotonic() - started,
           "stdout": stdout, "stderr": stderr,
           "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr)}
    common = (result.returncode == expected and not stderr and
              re.search(r"^# tests 1$", stdout, re.M) and
              re.search(r"^# cancelled 0$", stdout, re.M) and
              re.search(r"^# skipped 0$", stdout, re.M) and
              re.search(r"^# todo 0$", stdout, re.M))
    if expected == 0:
        valid = (common and re.search(r"^ok 1 - " + re.escape(case) + r"$", stdout, re.M)
                 and re.search(r"^# pass 1$", stdout, re.M)
                 and re.search(r"^# fail 0$", stdout, re.M))
    else:
        valid = (common and re.search(r"^not ok 1 - " + re.escape(case) + r"$", stdout, re.M)
                 and re.search(r"^# pass 0$", stdout, re.M)
                 and re.search(r"^# fail 1$", stdout, re.M)
                 and "code: 'ERR_ASSERTION'" in stdout
                 and "name: 'AssertionError'" in stdout
                 and (re.search(r"^    " + re.escape(case) + r"$", stdout, re.M)
                      or re.search(r"^  error: '" + re.escape(case) + r"'$", stdout, re.M)))
    row["accepted_phase"] = bool(valid)
    return row


def run(only=None):
    definitions = json.loads(DEFINITIONS.read_text(encoding="utf-8"))
    names = [row["name"] for row in definitions]
    if len(names) != len(set(names)) or (only and only not in names):
        raise ValueError("T476_WITHDRAWAL_EXACT_NAME")
    saved = {path: (ROOT / path).read_bytes() for path in PRODUCTS}
    inputs = {path: digest(data) for path, data in saved.items()}
    for path in (*SUITES, str(DEFINITIONS.relative_to(ROOT)), str(Path(__file__).relative_to(ROOT))):
        inputs[path] = digest((ROOT / path).read_bytes())
    report = {"schema": "r11-t1-withdrawal/1", "acceptance": False,
              "authority": "local Node VM diagnostic, not Chrome/native CI evidence",
              "limits_seconds": {"phase": PHASE_LIMIT_SECONDS, "total": TOTAL_LIMIT_SECONDS},
              "inputs_sha256": inputs, "rows": [], "ok": False}
    deadline = time.monotonic() + TOTAL_LIMIT_SECONDS
    with tempfile.TemporaryDirectory(prefix="r11-t1-withdrawal-") as directory:
        root = Path(directory)
        for path, data in saved.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        for definition in definitions:
            if only and definition["name"] != only:
                continue
            path, suite = definition["path"], definition["suite"]
            if path not in PRODUCTS[1:] or suite not in SUITES:
                raise ValueError("T476_WITHDRAWAL_SCOPE")
            original = saved[path]
            before, after = definition["before"].encode(), definition["after"].encode()
            if not before or before == after or original.count(before) != 1:
                raise ValueError("T476_WITHDRAWAL_UNIQUE_ANCHOR: " + definition["name"])
            mutated = original.replace(before, after, 1)
            target = root / path
            row = {"name": definition["name"], "case": definition["case"], "path": path,
                   "before_sha256": digest(original), "mutant_sha256": digest(mutated), "phases": []}
            report["rows"].append(row)
            try:
                row["phases"].append(phase(root, suite, definition["case"], 0, deadline))
                if not row["phases"][-1]["accepted_phase"]:
                    break
                target.write_bytes(mutated)
                row["phases"].append(phase(root, suite, definition["case"], 1, deadline))
            finally:
                target.write_bytes(original)
                row["restored_bytes_equal"] = target.read_bytes() == original
                row["restored_sha256"] = digest(target.read_bytes())
            row["phases"].append(phase(root, suite, definition["case"], 0, deadline))
            row["ok"] = row["restored_bytes_equal"] and all(p["accepted_phase"] for p in row["phases"])
            if not row["ok"]:
                break
    report["source_unchanged"] = all((ROOT / path).read_bytes() == data for path, data in saved.items())
    report["ok"] = (len(report["rows"]) == (1 if only else len(definitions)) and
                    all(row.get("ok", False) for row in report["rows"]) and report["source_unchanged"])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="one exact named withdrawal")
    parser.add_argument("--out", type=Path, help="new JSON diagnostic outside the repository")
    args = parser.parse_args()
    if args.out and (args.out.resolve() == ROOT or ROOT in args.out.resolve().parents):
        parser.error("--out must be outside the repository")
    report = run(args.only)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        print(json.dumps({"ok": report["ok"], "out": str(args.out),
                          "rows": [{"name": row["name"], "case": row["case"],
                                    "exits": [p["exit_code"] for p in row["phases"]],
                                    "ok": row.get("ok", False)} for row in report["rows"]]}, ensure_ascii=False))
    else:
        print(text, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
