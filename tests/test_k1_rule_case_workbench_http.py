"""Main K1 increment, independently counted without changing the existing suite.

The original fixture functions are shared verbatim. This class inherits only
unittest.TestCase, so none of the original suite's tests are run a second time.
"""
import unittest
from tests import test_rule_case_workbench_http as baseline

deepcopy=baseline.deepcopy
DATA_SCHEMA=baseline.DATA_SCHEMA
cases=baseline.cases
case=baseline.case
_Child=baseline._Child
patch=baseline.patch

class K1WorkbenchHTTP(unittest.TestCase):
    setUpClass=classmethod(baseline.WorkbenchHTTP.setUpClass.__func__)
    setUp=baseline.WorkbenchHTTP.setUp
    tearDown=baseline.WorkbenchHTTP.tearDown
    raw=baseline.WorkbenchHTTP.raw
    post=baseline.WorkbenchHTTP.post
    run_case=baseline.WorkbenchHTTP.run_case
    assert_reaped=baseline.WorkbenchHTTP.assert_reaped

    def test_new_receipt_projection_roundtrip_and_foreign_terminal_rejection(self):
        status, native = self.run_case("one-local-joint-new-version")
        self.assertEqual(status, 200, native)
        receipt = native["receipt"]
        self.assertEqual(receipt["status"], "passed", receipt)
        effective = receipt["observations"]["before"]["bindings"][0]["effective"][0]["A"]
        self.assertEqual(set(effective), {"value", "path"})
        bundle = {"schema": DATA_SCHEMA, "definitions": cases(),
                  "receipts": [{"definition": case("one-local-joint-new-version"), "receipt": receipt}]}
        for action in ("assess", "import"):
            status, result = self.post(action, sessionId=self.session, data=bundle)
            self.assertEqual(status, 200, result)
            self.assertEqual(result["data"], bundle)
        foreign = deepcopy(bundle)
        foreign["receipts"][0]["receipt"]["observations"]["before"]["bindings"][0]["effective"][0]["A"]["terminal"] = {"kind": "literal"}
        for action in ("assess", "import"):
            status, result = self.post(action, sessionId=self.session, data=foreign)
            self.assertEqual(status, 400, result)
            self.assertEqual(result["code"], "RECEIPT")


    def test_rejected_native_terminal_only_drift_is_not_hidden_by_projection(self):
        original = _Child.command
        reads = []
        def change_terminal(child, command):
            reply = original(child, command)
            if command == "assembly-read" and reply.get("state", {}).get("bindings"):
                reads.append(deepcopy(reply))
                if len(reads) >= 3:
                    reply["state"]["bindings"][0]["effective"][0]["A"]["terminal"] = {"kind": "spec"}
            return reply
        with patch.object(_Child, "command", change_terminal):
            status, native = self.run_case("wrong-type-dimension-reference")
        self.assertEqual(status, 200, native)
        self.assertGreaterEqual(len(reads), 3)
        self.assertEqual(native["receipt"]["status"], "failed", native)
        self.assertEqual(native["receipt"]["reason"], "rejected-world-changed", native)


if __name__ == '__main__':
    unittest.main()
