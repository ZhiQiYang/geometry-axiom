"""以原始 Q38 裁判執行交接控制，保留原始結束碼並核對預期結果。"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time


EXPECTED = {
    "XC36": ("survived", 0),
    "XC39": ("survived", 0),
    "XC40A": ("unlabelled", 1),
    "XC40B": ("survived", 0),
    "XC28L1": ("survived", 0),
    "XC28L12": ("survived", 0),
    "XC28L13": ("survived", 0),
    "XC29L1": ("survived", 0),
    "XC29L12": ("survived", 0),
    "XC29L13": ("survived", 0),
    "XC03L1": ("unlabelled", 1),
    "XC04L1": ("unlabelled", 1),
}


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model-base", type=Path, required=True)
    parser.add_argument("--controls", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    controls, model = args.controls.resolve(), args.model_base.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / "tmp").mkdir()
    resource.setrlimit(resource.RLIMIT_STACK, (16 * 1024 * 1024, resource.getrlimit(resource.RLIMIT_STACK)[1]))
    before = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
    if before:
        raise RuntimeError("控制執行前工作樹必須乾淨：" + before)
    variables = {
        "TMPDIR": str(out / "tmp"), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
        "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1",
        "GEOMETRY_MODEL_BASE": str(model),
    }
    command = [sys.executable, "-B", "-u", str(controls), "--jobs", str(args.jobs),
               "--receipt", str(out / "receipt.json"), "--logs", str(out / "logs")]
    for identifier in EXPECTED:
        command.extend(["--only", identifier])
    record = {
        "source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "root": str(root), "command": command, "environment": variables,
        "stack_bytes": resource.getrlimit(resource.RLIMIT_STACK)[0],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "controls_sha256": hashlib.sha256(controls.read_bytes()).hexdigest(),
        "model_base_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
        "status_before": before,
        "expected": {name: {"verdict": values[0], "exit": values[1]} for name, values in EXPECTED.items()},
    }
    save(out / "run-receipt.json", record)
    started = time.monotonic()
    with (out / "controls.log").open("wb") as log:
        process = subprocess.run(command, cwd=root, env={**os.environ, **variables}, stdout=log, stderr=subprocess.STDOUT)
    record.update(gate_exit_code=process.returncode, seconds=time.monotonic() - started,
                  ended_at=datetime.now(timezone.utc).isoformat())
    record["status_after"] = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
    record["restored"] = not record["status_after"]
    matched = False
    if (out / "receipt.json").exists():
        receipt = json.loads((out / "receipt.json").read_text(encoding="utf-8"))
        actual = {row["id"]: (row["verdict"], row["exit"]) for row in receipt["results"]}
        baselines_green = len(receipt["baselines"]) == 2 and all(
            baseline["exit"] == 0 and all(baseline["exception_evidence"][field] == 0
                for field in ("failures", "errors", "skipped"))
            for baseline in receipt["baselines"].values())
        matched = process.returncode == 1 and actual == EXPECTED and baselines_green and record["restored"]
        record.update(actual={name: {"verdict": value[0], "exit": value[1]} for name, value in actual.items()},
                      baselines_green=baselines_green)
    record["expected_matched"] = matched
    record["control_check_exit_code"] = 0 if matched else 1
    save(out / "run-receipt.json", record)
    print("原始裁判結束碼", process.returncode, "控制核對結束碼", record["control_check_exit_code"], flush=True)
    return record["control_check_exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
