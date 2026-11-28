"""The PF5 diagnostic evidence driver must reject unrelated reds and timeouts."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import pf5_geometry_mutations as driver


class PF5MutationEvidence(unittest.TestCase):
    TEST = "PF5GeometryOracle.test_named_subject"
    ASSERTION = "PF5_EXPECTED_ASSERTION"

    def evidence(self):
        return {"exit": 1, "timedOut": False,
                "unittest": {"events": [{"kind": "assertion-failure", "test": self.TEST,
                                          "exception": "builtins.AssertionError",
                                          "message": "comparison failed : "+self.ASSERTION}],
                             "testsRun": 1, "failures": 1, "errors": 0,
                             "skipped": 0, "unexpectedSuccesses": 0}}

    def test_exact_selected_test_and_named_assertion_are_required(self):
        valid = self.evidence()
        self.assertTrue(driver.expected_failure(valid, self.TEST, self.ASSERTION), "PF5_EXACT_FAILURE_ACCEPTED")
        for name, alter in [
            ("wrong-test", lambda r: r["unittest"]["events"][0].update(test="PF5GeometryOracle.test_other")),
            ("generic-assertion", lambda r: r["unittest"]["events"][0].update(message="False is not true")),
            ("partial-marker", lambda r: r["unittest"]["events"][0].update(message=self.ASSERTION+"_OTHER")),
            ("generic-error", lambda r: r["unittest"]["events"][0].update(kind="execution-error", exception="builtins.RuntimeError")),
            ("subclass-or-crash", lambda r: r["unittest"]["events"][0].update(exception="tests._bridge.BridgeClosed")),
            ("setup-error", lambda r: r["unittest"].update(errors=1)),
            ("skipped", lambda r: r["unittest"].update(skipped=1)),
            ("extra-test", lambda r: r["unittest"].update(testsRun=2)),
            ("signal-exit", lambda r: r.update(exit=-9)),
            ("timeout", lambda r: r.update(exit=124, timedOut=True)),
            ("unstructured-log", lambda r: r.update(unittest=None, raw="FAIL: "+self.TEST+"\nAssertionError: "+self.ASSERTION)),
        ]:
            with self.subTest(name=name):
                invalid = copy.deepcopy(valid)
                alter(invalid)
                self.assertFalse(driver.expected_failure(invalid, self.TEST, self.ASSERTION),
                                 "PF5_UNRELATED_RED_CANNOT_KILL: "+name)

    def test_real_worker_records_named_assertion_and_rejects_runtime_error(self):
        with tempfile.TemporaryDirectory(prefix="pf5-runner-contract-") as temporary:
            directory = Path(temporary)
            subject = directory/driver.FILES[0]
            subject.write_text("import unittest\nclass PF5GeometryOracle(unittest.TestCase):\n"
                               " def test_named_subject(self):\n  self.assertTrue(False, 'PF5_EXPECTED_ASSERTION')\n",
                               encoding="utf-8")
            named = driver.run(directory, directory/"named.log", self.TEST)
            self.assertTrue(driver.expected_failure(named, self.TEST, self.ASSERTION), "PF5_REAL_NAMED_WORKER")
            subject.write_text("import unittest\nclass PF5GeometryOracle(unittest.TestCase):\n"
                               " def test_named_subject(self):\n  raise RuntimeError('PF5_EXPECTED_ASSERTION')\n",
                               encoding="utf-8")
            error = driver.run(directory, directory/"error.log", self.TEST)
            self.assertEqual(1, error["exit"], "PF5_UNRELATED_ERROR_HAS_RED_EXIT")
            self.assertFalse(driver.expected_failure(error, self.TEST, self.ASSERTION), "PF5_RUNTIME_ERROR_NOT_KILL")
            self.assertEqual(1, error["unittest"]["errors"], "PF5_ERROR_IS_STRUCTURED")

    def test_baseline_and_restoration_require_one_real_passing_test(self):
        valid = {"exit": 0, "timedOut": False, "unittest": {"events": [], "testsRun": 1,
                 "success": True, "failures": 0, "errors": 0, "skipped": 0, "unexpectedSuccesses": 0, "expectedFailures": 0}}
        self.assertTrue(driver.successful_run(valid), "PF5_REAL_PASS_ACCEPTED")
        for name, change in [("skipped", {"skipped": 1}), ("not-run", {"testsRun": 0}),
                             ("expected-failure", {"expectedFailures": 1}), ("unexpected-success", {"unexpectedSuccesses": 1})]:
            with self.subTest(name=name):
                changed = copy.deepcopy(valid)
                changed["unittest"].update(change)
                self.assertFalse(driver.successful_run(changed), "PF5_EXIT_ZERO_ALONE_IS_NOT_GREEN")

    def test_real_worker_timeout_is_bounded_and_not_a_kill(self):
        with tempfile.TemporaryDirectory(prefix="pf5-runner-timeout-") as temporary:
            directory = Path(temporary)
            (directory/driver.FILES[0]).write_text(
                "import unittest,time\nclass PF5GeometryOracle(unittest.TestCase):\n"
                " def test_named_subject(self):\n  time.sleep(20)\n", encoding="utf-8")
            result = driver.run(directory, directory/"timeout.log", self.TEST, timeout=0.25)
            self.assertEqual(124, result["exit"], "PF5_TIMEOUT_EXIT_CLASSIFICATION")
            self.assertTrue(result["timedOut"], "PF5_TIMEOUT_EXPLICIT")
            self.assertLess(result["elapsedSeconds"], 5, "PF5_TIMEOUT_MUST_STOP_CHILD")
            self.assertFalse(driver.expected_failure(result, self.TEST, self.ASSERTION), "PF5_TIMEOUT_NOT_KILL")
            self.assertIn("PF5_DIAGNOSTIC_TIMEOUT", (directory/"timeout.log").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
