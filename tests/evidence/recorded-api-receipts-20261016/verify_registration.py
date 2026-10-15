"""Execute only the registered task-30 suite through run_all.run_suite.

This exercises the real aggregate adapter and expected count. It deliberately
does not claim a complete registry check or complete native run.
"""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests"))
import run_all


def main():
    name = "py:test_recorded_api_receipts"
    suites = [suite for suite in run_all.build_suites() if suite.name == name]
    assert len(suites) == 1 and suites[0].needs == [], "T1_REGISTERED_WITHOUT_NATIVE_BINARIES"
    row = run_all.run_suite(suites[0], os.environ.copy(), {})
    expected = json.loads((ROOT / "tests/run_all.expected.json").read_text(encoding="utf-8"))["suites"][name]
    print(json.dumps({"suite": name, "expected": expected, "row": vars(row)}, ensure_ascii=False, indent=2))
    assert row.total == row.passed == expected["count"] == 6
    assert row.failed == row.skipped == 0 and not row.crashed and not row.env_problem


if __name__ == "__main__":
    main()
