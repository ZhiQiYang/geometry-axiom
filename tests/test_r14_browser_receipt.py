"""Receipt-gate controls only; synthetic receipts do not prove browser execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github/scripts/check_r14_browser_receipt.py"
SPEC = importlib.util.spec_from_file_location("r14_browser_receipt", SCRIPT)
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def result(count=1):
    return {"schema": "geometry-cdp-result/1", "completed": True,
            "scope": {"mode": "partial", "filters": [GATE.FLAG], "modifiers": []},
            "passedAssertions": count, "failedAssertions": 0, "skipped": [],
            "sections": {"P381": count}, "sectionOrder": ["P381"],
            "goldenCompare": "not compared (partial mode)",
            "uncaughtBrowserExceptions": 0, "unexpectedBrowserExceptions": 0}


def log(value):
    return b"diagnostic output\nCDP_RESULT " + json.dumps(value).encode() + b"\n"


class R14BrowserReceipt(unittest.TestCase):
    def rejects(self, value, reason, exit_code=0):
        receipt = GATE.check_log(log(value), exit_code)
        self.assertFalse(receipt["passed"])
        self.assertTrue(any(reason in item for item in receipt["problems"]), receipt)

    def test_accepts_observed_positive_count_without_a_guessed_golden(self):
        for count in (1, 47):
            with self.subTest(count=count):
                receipt = GATE.check_log(log(result(count)), 0)
                self.assertTrue(receipt["passed"], receipt)
                self.assertEqual(receipt["observed"]["sections"], {"P381": count})
                self.assertEqual(receipt["problems"], [])

    def test_missing_duplicate_and_malformed_results_reject(self):
        for raw in (b"", log(result()) * 2, b"CDP_RESULT {broken}\n",
                    b"CDP_RESULT []\n", b'CDP_RESULT {"x":1,"x":2}\n',
                    b'CDP_RESULT {"x":NaN}\n'):
            with self.subTest(raw=raw):
                self.assertFalse(GATE.check_log(raw, 0)["passed"])

    def test_green_payload_cannot_hide_nonzero_process_exit(self):
        for code in (1, 137, None, False):
            with self.subTest(code=code):
                self.rejects(result(), "exit 0", code)

    def test_incomplete_fatal_and_wrong_schema_reject(self):
        for field, value, reason in (("completed", False, "complete"),
                                     ("completed", 1, "complete"),
                                     ("fatal", "browser died", "complete"),
                                     ("schema", "unknown/1", "schema")):
            with self.subTest(field=field, value=value):
                item = result(); item[field] = value
                self.rejects(item, reason)

    def test_only_exact_r14_partial_scope_is_accepted(self):
        scopes = [None, {}, {"mode": "full", "filters": [], "modifiers": []},
                  {"mode": "shard", "filters": [], "modifiers": []},
                  {"mode": "partial", "filters": ["GEOMETRY_GRID_SYSTEM_ONLY"], "modifiers": []},
                  {"mode": "partial", "filters": [GATE.FLAG, "OTHER"], "modifiers": []},
                  {"mode": "partial", "filters": [GATE.FLAG], "modifiers": ["OTHER"]}]
        for scope in scopes:
            with self.subTest(scope=scope):
                item = result(); item["scope"] = scope
                self.rejects(item, "Scope")

    def test_missing_empty_extra_and_noninteger_section_counts_reject(self):
        for sections in (None, {}, {"P381": 0}, {"P381": -1}, {"P381": True},
                         {"P381": "1"}, {"P381": 1, "P87": 1}):
            with self.subTest(sections=sections):
                item = result(); item["sections"] = sections
                self.rejects(item, "P381 section")

    def test_count_mismatch_and_wrong_section_order_reject(self):
        for value in (0, 2, True, "1"):
            with self.subTest(value=value):
                item = result(); item["passedAssertions"] = value
                self.rejects(item, "total")
        item = result(); item["sectionOrder"] = []
        self.rejects(item, "only executed section")

    def test_failures_skips_and_browser_exceptions_cannot_be_hidden(self):
        for field in ("failedAssertions", "uncaughtBrowserExceptions", "unexpectedBrowserExceptions"):
            for value in (1, False, "0", None):
                with self.subTest(field=field, value=value):
                    item = result(); item[field] = value
                    self.rejects(item, field)
        for field, value, reason in (("skipped", ["P381"], "skipped"),
                                     ("skipped", None, "skipped"),
                                     ("sectionsFailed", {"P381": 1}, "failed sections"),
                                     ("goldenCompare", "matched", "golden")):
            item = result(); item[field] = value
            self.rejects(item, reason)

    def test_cli_records_raw_log_digest_and_real_exit_status(self):
        with tempfile.TemporaryDirectory(prefix="r14-receipt-test-") as directory:
            root = Path(directory); source = root / "cdp.log"; target = root / "verified.json"
            raw = log(result()); source.write_bytes(raw)
            command = [sys.executable, str(SCRIPT), "--log", str(source),
                       "--commit", "a" * 40, "--out", str(target), "--exit-code"]
            for code in (0, 1):
                process = subprocess.run([*command, str(code)], capture_output=True)
                receipt = json.loads(target.read_text())
                self.assertEqual(process.returncode, code)
                self.assertEqual(receipt["exitCode"], code)
                self.assertEqual(receipt["sourceHead"], "a" * 40)
                self.assertEqual(receipt["logSha256"], hashlib.sha256(raw).hexdigest())

    def test_cli_missing_log_stays_red_and_writes_failure_receipt(self):
        with tempfile.TemporaryDirectory(prefix="r14-receipt-missing-") as directory:
            root = Path(directory); target = root / "verified.json"
            process = subprocess.run([sys.executable, str(SCRIPT), "--log", str(root / "missing.log"),
                "--commit", "a" * 40, "--out", str(target), "--exit-code", "0"], capture_output=True)
            self.assertEqual(process.returncode, 1)
            self.assertFalse(json.loads(target.read_text())["passed"])


if __name__ == "__main__":
    unittest.main()
