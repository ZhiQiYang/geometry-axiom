"""在隔離工作樹執行原始 Q38／§7 裁判，保存命令與原始紀錄。"""
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


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", choices=("q38", "card", "axiom"))
    parser.add_argument("--root", type=Path, default=Path("/workspace/geo261-gates"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    temp = out / "tmp"
    temp.mkdir()
    binary_dir = out.parent / "bin"
    binary_dir.mkdir(exist_ok=True)
    resource.setrlimit(resource.RLIMIT_STACK, (16 * 1024 * 1024, resource.getrlimit(resource.RLIMIT_STACK)[1]))
    variables = {
        "TMPDIR": str(temp),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "GEOMETRY_MODEL_BASE": str(binary_dir / "model-base"),
    }
    env = {**os.environ, **variables}
    status_before = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
    if status_before:
        raise RuntimeError("驗證前工作樹必須乾淨：" + status_before)
    record = {
        "source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "entry": args.entry,
        "root": str(root),
        "started_at": utc(),
        "environment": variables,
        "stack_bytes": resource.getrlimit(resource.RLIMIT_STACK)[0],
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "status_before": status_before,
        "commands": [],
    }

    def run(label, command):
        item = {"label": label, "command": command, "started_at": utc()}
        record["commands"].append(item)
        write_json(out / "run-receipt.json", record)
        started = time.monotonic()
        with (out / (label + ".log")).open("wb") as log:
            process = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
        item.update(exit_code=process.returncode, seconds=time.monotonic() - started, ended_at=utc())
        write_json(out / (label + ".command.json"), item)
        write_json(out / "run-receipt.json", record)
        print(label, "結束碼", process.returncode, "秒", round(item["seconds"], 3), flush=True)
        return process.returncode

    code = 0
    try:
        if args.entry in ("q38", "axiom"):
            code = run("build-model-base", [sys.executable, "-B", "-c",
                "import sys; from pathlib import Path; from tests import binaries; "
                "binaries.OUT_DIR = Path(sys.argv[1]); "
                "raise SystemExit(binaries.main(['build', 'model-base']))", str(binary_dir)])
        if code == 0:
            if args.entry == "q38":
                command = [sys.executable, "-B", "-u", "tests/section_profile_mutation_check.py",
                    "--jobs", str(args.jobs), "--receipt", str(out / "receipt.json"),
                    "--logs", str(out / "logs")]
            elif args.entry == "card":
                command = [sys.executable, "-B", "-u", "geometry-core/card-reference/run_mutations.py",
                    "--output", str(out / "raw")]
            else:
                command = [sys.executable, "-B", "-u", "geometry-core/card-reference/run_axiom_mutations.py",
                    "--output", str(out / "raw")]
            code = run(args.entry, command)
    finally:
        record["ended_at"] = utc()
        record["exit_code"] = code
        record["status_after"] = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
        record["restored"] = not record["status_after"]
        write_json(out / "run-receipt.json", record)
        if record["status_after"]:
            raise RuntimeError("驗證後工作樹未還原：" + record["status_after"])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
