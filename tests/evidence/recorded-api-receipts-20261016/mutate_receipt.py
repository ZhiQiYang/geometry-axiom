"""Reproduce cache-reuse removal against the unchanged six-test oracle.

Only a temporary source copy is mutated; no server/native process is started.
Exit 0 requires baseline green, a named assertion failure without errors/skips,
and restored green. Each child's actual exit/stdout/stderr and JSON are saved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    original = (ROOT / "geometry-web/serve.py").read_bytes()
    before = b"cached = native.api_receipts.get(request_id)"
    after = b"cached = None  # mutation: ignore all recorded results"
    assert original.count(before) == 1, "mutation target must be unique"
    test = Path("tests/test_recorded_api_receipts.py")
    runner = Path("tests/_unittest_runner.py")
    records = {}
    with tempfile.TemporaryDirectory(prefix="geometry-receipt-mutant-") as scratch:
        isolated = Path(scratch)
        for relative in (test, runner, Path("tests/binaries.py")):
            destination = isolated / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        source = isolated / "geometry-web/serve.py"
        source.parent.mkdir()
        for phase, content in (("baseline", original),
                               ("mutant", original.replace(before, after)),
                               ("restored", original)):
            source.write_bytes(content)
            result_path = (args.out / (phase + ".json")).resolve()
            argv = [sys.executable, str(isolated / runner), str(isolated / test),
                    "--json-out", str(result_path),
                    "--log", str((args.out / (phase + ".unittest.log")).resolve())]
            started = time.monotonic()
            result = subprocess.run(argv, capture_output=True, timeout=60, cwd=isolated)
            (args.out / (phase + ".stdout")).write_bytes(result.stdout)
            (args.out / (phase + ".stderr")).write_bytes(result.stderr)
            data = json.loads(result_path.read_text(encoding="utf-8"))
            records[phase] = {"actual_exit": result.returncode,
                              "seconds": time.monotonic() - started,
                              "source_sha256": hashlib.sha256(content).hexdigest(),
                              "test_sha256": hashlib.sha256((isolated / test).read_bytes()).hexdigest(),
                              "result": data}
            print(phase, "exit", result.returncode, "total", data["total"],
                  "passed", data["passed"], "failed", data["failed"], "skipped", data["skipped"])
        assert (ROOT / "geometry-web/serve.py").read_bytes() == original
    (args.out / "receipt.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for phase in ("baseline", "restored"):
        r = records[phase]
        assert r["actual_exit"] == 0 and r["result"]["passed"] == 6 and r["result"]["failed"] == 0
        assert r["result"]["skipped"] == 0
    r = records["mutant"]
    assert r["actual_exit"] == 1 and r["result"]["failed"] > 0
    assert r["result"]["skipped"] == 0 and r["result"]["extra_errors"] == 0
    assert not r["result"]["import_error"] and r["result"]["blocked_by_error"] == 0
    log = (args.out / "mutant.unittest.log").read_text(encoding="utf-8")
    assert "T1_LOST_RESPONSE_RECOVERED" in log and "ERROR:" not in log
    assert len({r["test_sha256"] for r in records.values()}) == 1
    print("PASS: unchanged oracle catches cache reuse removal; original source untouched")


if __name__ == "__main__":
    main()
