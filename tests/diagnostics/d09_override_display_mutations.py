"""D09 display withdrawals: a real Node assertion must prove each 0/1/0.

The production checkout is read-only. Mutants are isolated copies of the actual
workspace; missing anchors, setup/syntax errors and timeouts never count as kills.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


CASES = [
    ("D09_DROP_NATIVE_OVERRIDE_PROJECTION",
     "if(!source)return {mode:'inherit',value:''};",
     "return {mode:'inherit',value:''};",
     "^D09 current literal face override", "D09_CURRENT_LITERAL_MODE"),
    ("D09_DROP_FIRST_EDIT_SOURCE_MODE",
     "face.overrides[field]={mode:setting.mode==='saved'?'inherit':setting.mode,value:setting.value??''};",
     "face.overrides[field]={};",
     "^D09 first value edit", "D09_FIRST_VALUE_EDIT_KEEPS_MODE"),
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    product = root / "geometry-web/engineering-workspace.js"
    judge = root / "tests/test_engineering_override_display.js"
    original = product.read_bytes()
    source = original.decode("utf-8")
    result = {"schema": "d09-override-display-withdrawals/1",
              "sourceSha256": digest(original), "testSha256": digest(judge.read_bytes()),
              "runnerSha256": digest(Path(__file__).read_bytes()), "cases": []}

    def run(label: str, target: Path, pattern: str | None = None):
        command = ["node", "--test", "--test-reporter=tap"]
        if pattern:
            command.append("--test-name-pattern=" + pattern)
        command.append(str(judge))
        started = time.monotonic()
        try:
            process = subprocess.run(command, cwd=root, env={**os.environ,
                "GEOMETRY_D09_WORKSPACE_SOURCE": str(target)}, capture_output=True,
                text=True, timeout=45)
            code, stdout, stderr = process.returncode, process.stdout, process.stderr
        except subprocess.TimeoutExpired:
            code, stdout, stderr = "timeout", "", "node exceeded the 45 s diagnostic bound\n"
        (out / (label + ".stdout")).write_text(stdout, encoding="utf-8", newline="\n")
        (out / (label + ".stderr")).write_text(stderr, encoding="utf-8", newline="\n")
        return {"exit": code, "seconds": time.monotonic() - started,
                "command": command, "sourceSha256": digest(target.read_bytes())}, stdout + stderr

    baseline, output = run("baseline", product)
    result["baseline"] = baseline
    result["ok"] = baseline["exit"] == 0 and "# pass 7" in output and "# skipped 0" in output
    if result["ok"]:
        for name, old, new, pattern, assertion in CASES:
            count = source.count(old)
            row = {"name": name, "assertion": assertion, "anchorCount": count}
            if count != 1:
                row["status"] = "missing-or-ambiguous-anchor"
                result["ok"] = False
                result["cases"].append(row)
                continue
            with tempfile.TemporaryDirectory(prefix="d09-withdrawal-") as temp:
                mutant = Path(temp) / "engineering-workspace.js"
                mutant.write_text(source.replace(old, new), encoding="utf-8", newline="\n")
                syntax = subprocess.run(["node", "--check", str(mutant)], cwd=root,
                                        capture_output=True, text=True, timeout=45)
                row["syntaxExit"] = syntax.returncode
                if syntax.returncode:
                    row["status"] = "invalid-syntax"
                    result["ok"] = False
                    result["cases"].append(row)
                    continue
                changed, failure = run(name, mutant, pattern)
            restored, restored_output = run(name + "-restored", product)
            row.update({"baselineExit": baseline["exit"], "withdrawal": changed,
                        "restored": restored, "exitSequence": [baseline["exit"], changed["exit"], restored["exit"]]})
            killed = changed["exit"] == 1 and assertion in failure and "ERR_ASSERTION" in failure and "# fail 1" in failure
            restored_green = restored["exit"] == 0 and "# pass 7" in restored_output and "# skipped 0" in restored_output
            row["status"] = "killed" if killed and restored_green else "unverified"
            result["ok"] = result["ok"] and killed and restored_green
            result["cases"].append(row)
    result["checkoutUnchanged"] = product.read_bytes() == original
    result["ok"] = result["ok"] and result["checkoutUnchanged"]
    (out / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
