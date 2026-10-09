"""The unregistered backend seam accepts finite data and keeps host scope separate."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
sys.path.insert(0, str(ROOT))

from rule_cases import CaseDefinitionError, run_case_request
from rule_cases.catalog import case
from rule_cases.definition import canonical
from tests._bridge import find_bridge


class RequestDefinitionGate(unittest.TestCase):
    def test_host_settings_and_scripts_cannot_be_supplied_as_case_fields(self):
        for field, value in (("binary", "/tmp/program"), ("cwd", "/tmp/project"),
                             ("projectId", "foreign-project"), ("generation", 9),
                             ("contextToken", "formal-token"), ("script", "reset")):
            definition = case("legal-rule")
            definition[field] = value
            with self.subTest(field=field), self.assertRaises(CaseDefinitionError):
                run_case_request(canonical(definition), project_id="host-project", generation=0,
                                 binary="/unavailable-test-binary")

    def test_invalid_and_duplicate_json_reject_before_runtime_lookup(self):
        body = canonical(case("legal-rule"))
        duplicate = body.replace(b'"schema":"rule-case/1"',
                                 b'"schema":"rule-case/1","schema":"rule-case/1"')
        for data in (duplicate, b"{}", b"not JSON", b"\xff", body.decode()):
            with self.subTest(data_type=type(data).__name__), self.assertRaises(CaseDefinitionError):
                run_case_request(data, project_id="host-project", generation=0,
                                 binary="/unavailable-test-binary")

    def test_unknown_runtime_is_returned_as_a_nonpass_receipt(self):
        receipt = run_case_request(canonical(case("legal-rule")), project_id="host-project",
                                   generation=4, binary="/unavailable-test-binary")
        self.assertEqual("unknown-runtime", receipt["status"])
        self.assertEqual({"projectId": "host-project", "generation": 4}, receipt["context"])
        self.assertIsNone(receipt["actualOutcome"])
        self.assertIsNone(receipt["conditions"]["nativePid"])


class NativeRequestSeam(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = find_bridge()

    def run_request(self, case_id, **settings):
        return run_case_request(canonical(case(case_id)), project_id="request-project",
                                generation=8, binary=self.binary, **settings)

    def test_true_native_result_echoes_host_scope_without_writing_input(self):
        definition = case("legal-rule")
        original = deepcopy(definition)
        body = canonical(definition)
        receipt = run_case_request(body, project_id="request-project", generation=8, binary=self.binary)
        self.assertEqual("passed", receipt["status"], receipt)
        self.assertEqual({"projectId": "request-project", "generation": 8}, receipt["context"])
        self.assertEqual(original, definition)
        self.assertEqual(body, canonical(definition))
        self.assertTrue(receipt["conditions"]["privateDirectoryRemoved"])
        # Tokens/temporary paths stay inside the executor; a host context token
        # is neither accepted from case JSON nor copied into the run receipt.
        for field in ("token", "contextToken", "binary", "path", "cwd"):
            self.assertNotIn(field, receipt)
        self.assertIsInstance(json.dumps(receipt, ensure_ascii=False), str)

    def test_precise_negative_passes_while_capability_and_cancellation_keep_nonpass_results(self):
        negative = self.run_request("fixed-version-immutable")
        self.assertEqual("passed", negative["status"], negative)
        self.assertEqual("rejected", negative["actualOutcome"])
        expected = {"code": "RULE_VERSION_IMMUTABLE", "clause": "D32",
                    "ref": {"kind": "rule", "id": 17, "version": 1}}
        actual = [{key: d.get(key) for key in ("code", "clause", "ref")}
                  for d in negative["actualDiagnostics"]]
        self.assertIn(canonical(expected), [canonical(d) for d in actual])
        self.assertTrue(negative["conditions"]["privateDirectoryRemoved"])
        cancelled = threading.Event()
        cancelled.set()
        receipt = self.run_request("legal-rule", cancel=cancelled)
        self.assertEqual(("blocked", "cancelled"), (receipt["status"], receipt["reason"]))
        self.assertTrue(receipt["conditions"]["privateDirectoryRemoved"])
        definition = case("legal-rule")
        definition["requiredCapabilities"].append("absent-request-capability/1")
        receipt = run_case_request(canonical(definition), project_id="request-project",
                                   generation=8, binary=self.binary)
        self.assertEqual("missing-capability", receipt["status"])


if __name__ == "__main__":
    unittest.main()
