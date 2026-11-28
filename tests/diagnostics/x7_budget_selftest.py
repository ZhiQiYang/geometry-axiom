#!/usr/bin/env python3
"""Small fabricated inputs testing the X7 budget checker, not product evidence.

make_fixture() is importable by the registered native suite. All 1 ms/10 ms
numbers below are deliberately synthetic checker examples, not scene budgets
or measurements. No production budget JSON is produced by this module.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import x7_budget as gate


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stat(value=1.0):
    return {"samples": [value], "count": 1, "min_ms": value, "median_ms": value,
            "p95_nearest_rank_ms": value, "max_ms": value}


def make_fixture(directory):
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    report = {"schema": "x7-performance-report/1", "acceptance": False,
              "argv": ["synthetic-checker-fixture", "--out", str(root)], "cwd": str(root),
              "clock": "perf_counter_ns", "method": deepcopy(gate.METHOD), "repeats": 1,
              "exit_code": 0, "cases": []}
    budget = {"schema": "x7-operation-budgets/1", "unit": "ms",
              "measurement_method": deepcopy(gate.METHOD), "cases": {}}
    for key, (count, room_count, batch) in gate.CASE_SPECS.items():
        operations = gate.expected_operations(key)
        budget["cases"][key] = {"count": count, "roomCount": room_count, "batchKind": batch,
            "operations": {operation: {"upper_ms": 10.0, "basis": "SYNTHETIC checker fixture only; not an observed budget"}
                           for operation in sorted(operations)}}
        references = {"ok": True, "timbers": [{"id": number} for number in range(1, count + 1)]}
        references_name = key + "-0.references.json"
        put(root / references_name, references)
        rows, stdin, stdout = [], [], []
        for operation in sorted(operations - {"native_save_as", "schedule_derive", "schedule_csv"}):
            command = ("line " + operation if operation in ("undo", "redo") else gate.COMMAND_HEADS[operation])
            if operation in {"native_load", "framing_preview", "import_prepare"}:
                command += " /synthetic-checker-input"
            elif operation in {"framing_confirm", "import_confirm"}:
                command += " 1"
            reply = references if operation == "bridge_references" else {"ok": True}
            raw = (json.dumps(reply) + "\n").encode()
            rows.append({"command": command, "operation": operation, "wire_ms": 1.0,
                         "json_parse_ms": .1, "reply_bytes": len(raw), "reply_sha256": gate.digest(raw),
                         "ok": True, "timeout_seconds": 60})
            stdin.append((command + "\n").encode())
            stdout.append(raw)
        prefix = root / "raw" / (key + "-0")
        prefix.parent.mkdir(exist_ok=True)
        Path(str(prefix) + ".stdin").write_bytes(b"".join(stdin))
        Path(str(prefix) + ".stdout").write_bytes(b"".join(stdout))
        Path(str(prefix) + ".stderr").write_bytes(b"")
        metrics = {"schema": "x7-dialogue/1", "acceptance": False, "label": key + "-0",
                   "command": ["synthetic-not-a-product"], "binary_sha256": "0" * 64,
                   "stack_bytes": 16 * 1024 * 1024, "child_exit": 0, "stderr_bytes": 0, "rows": rows}
        put(Path(str(prefix) + ".metrics.json"), metrics)
        scene = b"# synthetic budget checker input, not a native scene receipt\n"
        (root / (key + "-0.saved.scene")).write_bytes(scene)
        sample = {"iteration": 0, "raw_prefix": "raw/" + key + "-0", "child_exit": 0, "stderr_bytes": 0,
                  "binary_sha256": "0" * 64, "rows": rows, "native_save_as_ms": 1.0,
                  "references_path": str(root / references_name), "completed_scene_sha256": gate.digest(scene)}
        csv = b'["synthetic checker CSV"]'
        schedule = {"schema": "x7-schedule-measurement/1", "acceptance": False, "node": "synthetic",
                    "references_sha256": gate.digest((root / references_name).read_bytes()),
                    "count": count, "surfaces": room_count, "csv_bytes": len(csv), "csv_sha256": gate.digest(csv),
                    "rows": [{"iteration": 0, "derive_ms": 1.0, "csv_ms": 1.0, "cold_module_sample": True}]}
        put(root / (key + ".schedule.json"), schedule)
        put(root / (key + ".schedule.stdout"), schedule)
        (root / (key + ".schedule.stderr")).write_bytes(b"")
        (root / (key + ".schedule.json.csv-array.json")).write_bytes(csv)
        case = {"key": key, "count": count, "roomCount": room_count, "batchKind": batch,
                "samples": [sample], "operations": {operation: stat() for operation in sorted(operations)},
                "schedule_command": ["node", "/synthetic/tests/diagnostics/x7_schedule_benchmark.cjs",
                                     str(root / references_name), "1", str(root / (key + ".schedule.json"))],
                "schedule_exit": 0, "schedule": schedule}
        report["cases"].append(case)
    return report, budget


class BudgetCheckerSelftest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="x7-budget-unit-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.report, self.budget = make_fixture(self.root)

    def reject(self, marker):
        with self.assertRaises(gate.BudgetFailure) as raised:
            gate.check_report(self.report, self.budget, self.root)
        self.assertEqual(marker, raised.exception.marker)

    def test_exact_complete_synthetic_report_passes(self):
        result = gate.check_report(self.report, self.budget, self.root)
        self.assertTrue(result["ok"])
        self.assertFalse(result["acceptance"])
        self.assertEqual(33, len(result["checks"]))

    def test_every_sample_upper_bound_is_enforced(self):
        self.budget["cases"]["house500"]["operations"]["framing_preview"]["upper_ms"] = .5
        self.reject("X7_BUDGET_EXCEEDED")

    def test_acceptable_median_cannot_hide_slow_tail_sample(self):
        record = {"samples": [1.0, 1.0, 11.0], "count": 3, "min_ms": 1.0,
                  "median_ms": 1.0, "p95_nearest_rank_ms": 11.0, "max_ms": 11.0}
        with self.assertRaises(gate.BudgetFailure) as raised:
            gate.checked_statistics(record, record["samples"], "house500", "framing_preview", 10.0)
        self.assertEqual("X7_BUDGET_EXCEEDED", raised.exception.marker)
        self.assertEqual(2, raised.exception.detail["sample"])
        self.assertEqual("framing_preview", raised.exception.detail["operation"])

    def test_missing_operation_is_rejected(self):
        del self.report["cases"][0]["operations"]["bridge_dump"]
        self.reject("X7_BUDGET_REPORT_OPERATIONS")

    def test_missing_scene_is_rejected(self):
        self.report["cases"].pop()
        self.reject("X7_BUDGET_REPORT_CASES")

    def test_wrong_case_and_sample_types_are_named_failures(self):
        original = self.report["cases"][0]
        self.report["cases"][0] = None
        self.reject("X7_BUDGET_REPORT_CASES")
        self.report["cases"][0] = original
        self.report["cases"][0]["samples"][0] = None
        self.reject("X7_BUDGET_SAMPLE_SCHEMA")

    def test_nan_negative_and_boolean_timing_are_rejected(self):
        for value in (float("nan"), float("inf"), -1, True):
            with self.subTest(value=value):
                self.report["cases"][0]["samples"][0]["native_save_as_ms"] = value
                self.reject("X7_BUDGET_SAVE_VALUE")

    def test_nonzero_child_is_rejected(self):
        self.report["cases"][0]["samples"][0]["child_exit"] = 1
        self.reject("X7_BUDGET_CHILD_EXIT")

    def test_raw_stderr_is_rejected(self):
        (self.root / "raw/room53-0.stderr").write_bytes(b"unexpected diagnostic\n")
        self.reject("X7_BUDGET_RAW_STDERR")

    def test_changed_measurement_boundary_is_rejected(self):
        self.report["method"]["cold"] = "discard first sample"
        self.reject("X7_BUDGET_MEASUREMENT_METHOD")

    def test_recomputed_statistics_cannot_hide_changed_raw_measurement(self):
        sample = self.report["cases"][0]["samples"][0]
        next(row for row in sample["rows"] if row["operation"] == "native_load")["wire_ms"] = 2.0
        self.report["cases"][0]["operations"]["native_load"] = stat(2.0)
        self.reject("X7_BUDGET_RAW_TIMINGS")

    def test_forged_maximum_is_recomputed(self):
        self.report["cases"][0]["operations"]["native_load"]["max_ms"] = .1
        self.reject("X7_BUDGET_STATISTIC_RECOMPUTED")

    def test_path_traversal_is_rejected(self):
        self.report["cases"][0]["samples"][0]["references_path"] = str(self.root / "../room53-0.references.json")
        self.reject("X7_BUDGET_RECORDED_PATH")

    def test_duplicate_json_key_and_nonfinite_json_are_rejected(self):
        for text, marker in ((b'{"a":1,"a":2}', "X7_BUDGET_DUPLICATE_JSON_KEY"),
                             (b'{"a":NaN}', "X7_BUDGET_NONFINITE_JSON")):
            with self.subTest(marker=marker), self.assertRaises(gate.BudgetFailure) as raised:
                gate.parse_json(text)
            self.assertEqual(marker, raised.exception.marker)

    def test_nonfinite_failure_detail_is_machine_readable(self):
        detail = gate.safe_detail({"bad": [float("nan"), float("inf"), -float("inf")]})
        self.assertEqual('{"bad": ["nan", "inf", "-inf"]}', json.dumps(detail, allow_nan=False))


if __name__ == "__main__":
    unittest.main()
