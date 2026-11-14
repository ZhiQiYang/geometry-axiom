"""Run named R14 App faults against the shipped workspace/preview functions.

Only temporary source copies are mutated; no product, assertion, golden or
mutation ledger is rewritten. Each fault needs a full 7-test green baseline,
an assertion failure in its named judge, and a full green restoration.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = "geometry-web/grid-system-workspace.js"
IMPACT = "geometry-web/reference-ui.js"
TEST = "tests/test_r14_app.js"
EXPECTED_TESTS = 7


def fault(identifier, path, before, after, judge):
    return {"id": identifier, "path": path, "before": before,
            "after": after, "judge": judge}


MUTANTS = [
    fault("R14_APP_PANEL_GATE_RESTORED", WORKSPACE,
          "!['repeat','repeat-panel'].includes(s.source[a+'Definition']?.source)",
          "s.source[a+'Definition']?.source!=='repeat'",
          "R14 App accepts both mixed axes and both PANEL axes with the full /2 host"),
    fault("R14_APP_FULL_HOST_GATE_REMOVED", WORKSPACE,
          "if(panelRules(s.source)&&!s.capabilities?.includes('grid-subdivision-rules/2'))return",
          "if(false&&panelRules(s.source)&&!s.capabilities?.includes('grid-subdivision-rules/2'))return",
          "R14 App requires full host /2 rather than a native-only profile"),
    fault("R14_APP_PENDING_HOST_RECHECK_REMOVED", WORKSPACE,
          "    if(panelRules(s.source)){\n"
          "      const host=await apiRequest('engineering-read');if(!current(s))return;\n"
          "      s.capabilities=host.ok&&Array.isArray(host.state?.capabilities)?host.state.capabilities:[];\n"
          "    }\n",
          "    // Fault: keep the capability observed when opening the editor.\n",
          "R14 App rechecks host capability before submitting a pending rule"),
    fault("R14_APP_PANEL_BODY_AS_PREVIEW_PITCH", IMPACT,
          "BigInt(d.panel ?? d.effectivePanel)+BigInt(d.gap)",
          "BigInt(d.panel ?? d.effectivePanel)",
          "R14 candidate summary uses full panel plus gap and native effective lengths"),
    fault("R14_APP_NATIVE_LINES_DISCARDED", WORKSPACE,
          "out.push(...result.rows);if(!result.complete)",
          "out.push(...[]);if(!result.complete)",
          "R14 App draws native full-pitch coordinates and retains preview-only identities"),
]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def run(node, env, folder, name):
    command = [node, "--test", "--test-reporter=tap", TEST]
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                            text=True, timeout=45, check=False)
    stdout = folder / f"{name}.stdout.tap"
    stderr = folder / f"{name}.stderr.txt"
    stdout.write_text(result.stdout, encoding="utf-8", newline="\n")
    stderr.write_text(result.stderr, encoding="utf-8", newline="\n")
    counts = {key: int(value) for key, value in
              re.findall(r"^# (tests|pass|fail|cancelled|skipped|todo) (\d+)$",
                         result.stdout, re.MULTILINE)}
    return {"command": command, "started_at": started,
            "returncode": result.returncode, "counts": counts,
            "stdout": str(stdout), "stderr": str(stderr)}, result.stdout


def full_run(row):
    count = row["counts"]
    return (count.get("tests") == EXPECTED_TESTS
            and count.get("cancelled") == 0 and count.get("skipped") == 0
            and count.get("todo") == 0)


def green(row):
    return (row["returncode"] == 0 and full_run(row)
            and row["counts"].get("pass") == EXPECTED_TESTS
            and row["counts"].get("fail") == 0)


def assertion_killed(row, output, judge):
    # A syntax/import error, uncaught application error, crash or timeout is
    # never an assertion kill. Require ERR_ASSERTION in the named TAP block.
    block = re.search(r"^not ok \d+ - " + re.escape(judge)
                      + r"\n(?P<body>.*?)(?=^# Subtest:|^1\.\.|\Z)",
                      output, re.MULTILINE | re.DOTALL)
    return (row["returncode"] == 1 and full_run(row) and block is not None
            and "code: 'ERR_ASSERTION'" in block.group("body")
            and "failureType: 'testCodeFailure'" in block.group("body"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    node = shutil.which("node")
    if not node:
        raise SystemExit("node is required")
    env = os.environ.copy()
    for key in ("GEOMETRY_R14_WORKSPACE_SOURCE", "GEOMETRY_R14_IMPACT_SOURCE"):
        env.pop(key, None)
    originals = {name: (ROOT / name).read_bytes() for name in (WORKSPACE, IMPACT, TEST)}
    receipt = {"schema": "r14-app-mutations/1", "status": "blocked",
               "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               "source_files": {name: {"bytes": len(data), "sha256": sha256(data)}
                                for name, data in originals.items()}, "mutants": []}
    try:
        for item in MUTANTS:
            folder = output / item["id"]
            folder.mkdir(parents=True, exist_ok=True)
            record = {"id": item["id"], "judge": item["judge"],
                      "path": item["path"], "status": "blocked"}
            receipt["mutants"].append(record)
            record["before"], _ = run(node, env, folder, "before")
            if not green(record["before"]):
                raise RuntimeError(f"{item['id']}: baseline is not full green")
            original = originals[item["path"]]
            before, after = item["before"].encode(), item["after"].encode()
            if original.count(before) != 1:
                raise RuntimeError(f"{item['id']}: expected one exact source anchor")
            mutated = original.replace(before, after, 1)
            record.update(before_sha256=sha256(original), mutated_sha256=sha256(mutated),
                          replaced_before=item["before"], replaced_after=item["after"])
            with tempfile.TemporaryDirectory(prefix=item["id"] + "-") as temporary:
                candidate = Path(temporary) / Path(item["path"]).name
                candidate.write_bytes(mutated)
                fault_env = env.copy()
                fault_env["GEOMETRY_R14_WORKSPACE_SOURCE" if item["path"] == WORKSPACE
                          else "GEOMETRY_R14_IMPACT_SOURCE"] = str(candidate)
                record["fault"], text = run(node, fault_env, folder, "fault")
                if not assertion_killed(record["fault"], text, item["judge"]):
                    raise RuntimeError(f"{item['id']}: named assertion did not kill the fault")
                candidate.write_bytes(original)
                record["restored"], _ = run(node, fault_env, folder, "restored")
                record["restored_sha256"] = sha256(candidate.read_bytes())
                if record["restored_sha256"] != record["before_sha256"] or not green(record["restored"]):
                    raise RuntimeError(f"{item['id']}: byte restoration is not full green")
            record["status"] = "killed"
            print(f"{item['id']}: green -> assertion red -> restored green", flush=True)
        if any((ROOT / name).read_bytes() != data for name, data in originals.items()):
            raise RuntimeError("working source changed while the probe was running")
        receipt["status"] = "passed"
    finally:
        (output / "results.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                                              encoding="utf-8", newline="\n")
    print(f"{len(MUTANTS)} killed; source files unchanged; {output / 'results.json'}")


if __name__ == "__main__":
    main()
