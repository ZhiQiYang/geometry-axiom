"""Real HTTP + verified disposable native process; no replacement rule engine.

Held-child tests wrap a lifecycle boundary and still call the original method.
Optional GEOMETRY_RULE_CASE_EVIDENCE_DIR writes synthetic raw evidence to TEMP.
"""
from copy import deepcopy
import http.client
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "geometry-web"))
from tests._bridge import BridgeSession, find_bridge
from rule_case_workbench_adapter import (DATA_SCHEMA, MAX_DATA_BYTES, MAX_RECEIPTS,
                                         PROTOCOL, RuleCaseWorkbenchAdapter)
from rule_case_workbench_standalone import WorkbenchServer
from rule_cases.catalog import case, cases
from rule_cases.executor import _Child


class WorkbenchHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = find_bridge()

    def setUp(self):
        self.context = {"projectId": "http-workbench-project", "generation": 7,
                        "contextToken": "original-http-context"}
        self.adapter = RuleCaseWorkbenchAdapter(capture_context=lambda: self.context, binary=self.binary)
        self.server = WorkbenchServer(("127.0.0.1", 0), self.adapter, self.context)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.session = self.post("open")[1]["sessionId"]

    def tearDown(self):
        self.adapter.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.assertFalse(self.thread.is_alive())
        self.assertIsNone(self.adapter.active)

    def raw(self, body, path="/rule-cases/workbench", headers=None):
        request = urllib.request.Request(self.base + path, data=body,
                                        headers=headers or {"Content-Type": "application/json"})
        try:
            response = urllib.request.urlopen(request, timeout=15)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def post(self, action, **fields):
        return self.raw(json.dumps({"protocol": PROTOCOL, "action": action, **fields}).encode())

    def run_case(self, case_id="legal-rule", run_id="native", definition=None):
        return self.post("run", sessionId=self.session, runId=run_id,
                         definition=definition or case(case_id))

    def assert_reaped(self, receipt):
        self.assertTrue(receipt["conditions"]["privateDirectoryRemoved"])
        pid = receipt["conditions"]["nativePid"]
        self.assertIsInstance(pid, int)
        if os.name != "nt":
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)

    def test_six_true_http_native_cases_and_exact_negative_oracles(self):
        receipts, outcomes = [], []
        before = set(Path(tempfile.gettempdir()).glob("geometry-rule-case-*"))
        for index, definition in enumerate(cases()):
            status, result = self.run_case(definition=definition, run_id=f"six-{index}")
            self.assertEqual(status, 200, result)
            self.assertEqual(result["trust"], "controlled-run")
            self.assertEqual(result["context"], self.context)
            receipt = result["receipt"]
            self.assertEqual(receipt["status"], "passed", receipt)
            outcomes.append(receipt["actualOutcome"])
            self.assert_reaped(receipt)
            self.assertTrue(all(a["passed"] for a in receipt["assertionResults"]))
            if definition["expect"]["outcome"] == "rejected":
                expected = definition["expect"]["diagnostic"]
                actual = [{k: d.get(k) for k in ("code", "clause", "ref")} for d in receipt["actualDiagnostics"]]
                self.assertIn(expected, actual)
                observation = receipt["observations"]
                self.assertEqual(observation["before"], observation["after"])
                self.assertEqual(observation["beforeDumpHash"], observation["afterDumpHash"])
                self.assertEqual(observation["beforeRevision"], observation["afterRevision"])
            receipts.append({"definition": definition, "receipt": receipt})
        self.assertEqual(outcomes.count("accepted"), 4)
        self.assertEqual(outcomes.count("rejected"), 2)
        self.assertEqual(before, set(Path(tempfile.gettempdir()).glob("geometry-rule-case-*")))
        directory = os.environ.get("GEOMETRY_RULE_CASE_EVIDENCE_DIR")
        if directory:
            path = Path(directory).resolve()
            self.assertTrue(path.is_relative_to(Path(tempfile.gettempdir()).resolve()))
            path.mkdir(parents=True, exist_ok=True)
            (path / "native.json").write_text(json.dumps({"schema": DATA_SCHEMA, "definitions": cases(),
                                                         "receipts": receipts}, ensure_ascii=False, indent=2))

    def test_finite_edit_changes_hash_and_preserves_independent_oracle(self):
        definition = case("legal-rule")
        original = deepcopy(definition)
        definition["label"] = "<script>this is text</script>"
        status, checked = self.post("validate", sessionId=self.session, definition=definition)
        self.assertEqual(status, 200, checked)
        definition["input"]["transaction"][0]["value"]["joints"][0]["side"] = "-u"
        status, result = self.run_case(definition=definition)
        self.assertEqual(status, 200)
        self.assertEqual(result["receipt"]["status"], "failed")
        self.assertEqual(result["receipt"]["reason"], "assertion-mismatch")
        self.assertEqual(original["assertions"], definition["assertions"])
        self.assert_reaped(result["receipt"])

    def test_import_self_consistent_forged_pass_remains_unverified_and_original_is_preserved(self):
        _, native = self.run_case()
        receipt = native["receipt"]
        bundle = {"schema": DATA_SCHEMA, "definitions": cases(),
                  "receipts": [{"definition": case("legal-rule"), "receipt": receipt}]}
        original = deepcopy(bundle)
        status, result = self.post("import", sessionId=self.session, data=bundle)
        self.assertEqual(status, 200, result)
        self.assertEqual(result["data"], original)
        self.assertEqual(result["views"][0]["trust"], "historical-unverified")
        self.assertEqual(result["views"][0]["receipt"]["status"], "passed")
        # Even fabricated process metadata with consistent core evidence cannot become current.
        bundle["receipts"][0]["receipt"]["conditions"]["nativePid"] = 123456
        status, result = self.post("import", sessionId=self.session, data=bundle)
        self.assertEqual(status, 200, result)
        self.assertEqual(result["views"][0]["trust"], "historical-unverified")

    def test_drift_view_preserves_original_definition_runtime_and_scope(self):
        _, native = self.run_case()
        receipt = native["receipt"]
        bundle = {"schema": DATA_SCHEMA, "definitions": cases(),
                  "receipts": [{"definition": case("legal-rule"), "receipt": receipt}]}
        bundle["definitions"][3]["label"] += "修改"
        original = deepcopy(bundle)
        _, result = self.post("assess", sessionId=self.session, data=bundle)
        view = result["views"][0]["receipt"]
        self.assertEqual(view["status"], "stale")
        self.assertIn("definition", view["staleReasons"])
        self.assertEqual(result["data"], original)
        # Captured scope cannot be renewed by rechecking under a new host token.
        self.context["generation"] += 1
        self.context["contextToken"] = "new-token"
        self.assertEqual(self.post("assess", sessionId=self.session, data=bundle)[1]["code"], "RETIRED")
        new = self.post("open")[1]["sessionId"]
        _, result = self.post("import", sessionId=new, data=bundle)
        self.assertIn("generation", result["views"][0]["receipt"]["staleReasons"])
        self.assertEqual(result["data"], original)

    def test_wrong_typed_or_missing_diagnostic_never_promotes_negative(self):
        _, native = self.run_case("wrong-type-dimension-reference")
        for diagnostic in [{"code": "ASSEMBLY_INVALID", "clause": "I40/I41", "ref": {}},
                           {"code": "DIMENSION_TYPE", "clause": "D33", "ref": {"kind": "parameter", "id": 41, "fieldId": True}}]:
            receipt = deepcopy(native["receipt"])
            receipt["actualDiagnostics"] = [diagnostic]
            bundle = {"schema": DATA_SCHEMA, "definitions": cases(),
                      "receipts": [{"definition": case("wrong-type-dimension-reference"), "receipt": receipt}]}
            status, result = self.post("import", sessionId=self.session, data=bundle)
            self.assertEqual(status, 400)
            self.assertFalse(result["ok"])

    def test_runtime_source_and_project_drift_keep_original_receipt_and_are_noncurrent(self):
        _, native = self.run_case("one-local-joint-new-version")
        receipt = native["receipt"]
        bundle = {"schema": DATA_SCHEMA, "definitions": cases(),
                  "receipts": [{"definition": case("one-local-joint-new-version"), "receipt": receipt}]}
        # Change the CURRENT exact setup value and recompute its private pin.
        from rule_cases.definition import digest
        current = bundle["definitions"][1]
        current["input"]["setup"][0]["value"]["name"] = "changed source name"
        current["sourcePins"][0]["sha256"] = digest(current["input"]["setup"][0]["value"])
        original = deepcopy(bundle)
        _, result = self.post("assess", sessionId=self.session, data=bundle)
        self.assertIn("source", result["views"][0]["receipt"]["staleReasons"])
        self.assertEqual(result["data"], original)
        self.adapter.binary = "/unknown-current-runtime"
        _, result = self.post("assess", sessionId=self.session, data=bundle)
        self.assertIn("unknown-runtime", result["views"][0]["receipt"]["staleReasons"])
        self.assertEqual(result["data"], original)
        self.adapter.binary = self.binary
        # Structurally valid forged runtime identity is stale, never authenticated.
        bundle["receipts"][0]["receipt"]["executor"]["nativeBinaryHash"] = "0" * 64
        _, result = self.post("import", sessionId=self.session, data=bundle)
        self.assertIn("runtime", result["views"][0]["receipt"]["staleReasons"])
        self.assertEqual(result["views"][0]["trust"], "historical-unverified")
        self.context["projectId"] = "B"
        self.adapter.invalidate()
        new = self.post("open")[1]["sessionId"]
        _, result = self.post("import", sessionId=new, data=bundle)
        self.assertIn("project-context", result["views"][0]["receipt"]["staleReasons"])

    def test_sessions_run_ids_and_expiry_are_bounded_without_permanent_open_close_leak(self):
        for index in range(64):
            self.assertEqual(self.post("cancel", sessionId=self.session, runId=f"retired-{index}")[0], 200)
        self.assertEqual(self.post("cancel", sessionId=self.session, runId="over-limit")[1]["code"], "CAPACITY")
        self.adapter.sessions[self.session]["started"] -= 301
        self.assertEqual(self.run_case()[1]["code"], "RETIRED")
        # Closed sessions are pruned; 100 normal opens/closes do not exhaust capacity.
        for _ in range(100):
            status, opened = self.post("open")
            self.assertEqual(status, 200, opened)
            self.post("close", sessionId=opened["sessionId"])
        for _ in range(16):
            self.assertEqual(self.post("open")[0], 200)
        self.assertEqual(self.post("open")[1]["code"], "CAPACITY")

    def test_case_run_and_cancel_leave_separate_native_world_and_pending_assembly_candidate(self):
        with tempfile.TemporaryDirectory(prefix="rule-case-formal-control-") as directory, BridgeSession(self.binary) as formal:
            formal.command("reset")
            transaction = {"schema": "assembly-transaction/1",
                           "expectedRevision": formal.command("assembly-read")["revision"],
                           "operations": case("legal-rule")["input"]["transaction"]}
            path = Path(directory) / "pending.json"
            path.write_text(json.dumps(transaction))
            preview = formal.command("assembly-preview " + str(path))["preview"]
            self.assertTrue(preview["valid"])
            before = formal.command("dump"), formal.command("assembly-read")
            self.held_child(lambda: self.post("cancel", sessionId=self.session, runId="held"))
            self.assertEqual(self.run_case(run_id="private-done")[0], 200)
            self.assertEqual(before, (formal.command("dump"), formal.command("assembly-read")))
            self.assertTrue(formal.command("assembly-confirm " + str(preview["token"]))["ok"])

    def test_malformed_unknown_and_bounded_data_reject_before_replacement(self):
        empty = {"schema": DATA_SCHEMA, "definitions": cases(), "receipts": []}
        variants = []
        for schema in ["geometry-canvas/14", "geometry-canvas/15", "rule-case-workbench-data/2"]:
            variants.append({**empty, "schema": schema})
        variants.extend([{**empty, "trust": "controlled-run"}, {**empty, "definitions": []},
                         {**empty, "receipts": [{}] * (MAX_RECEIPTS + 1)},
                         {**empty, "receipts": [{"definition": case("legal-rule"), "receipt": {"status": "passed"}}]}])
        bad = deepcopy(empty); bad["definitions"][1]["sourcePins"][0]["sha256"] = "0" * 64
        variants.append(bad)
        for data in variants:
            with self.subTest(data=list(data)):
                self.assertFalse(self.post("import", sessionId=self.session, data=data)[1]["ok"])
        # Send headers first: a server may close before an oversized client body
        # is sent, which urllib correctly reports as a broken pipe.
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.putrequest("POST", "/rule-cases/workbench")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", str(MAX_DATA_BYTES + 1))
        connection.endheaders()
        self.assertEqual(connection.getresponse().status, 413)
        connection.close()

    def test_host_overrides_scripts_duplicate_fields_and_unsupported_route_reject(self):
        valid = {"protocol": PROTOCOL, "action": "run", "sessionId": self.session,
                 "runId": "bad", "definition": case("legal-rule")}
        for key, value in [("binary", self.binary), ("projectId", "B"), ("generation", 9),
                           ("contextToken", "renewed"), ("script", "reset")]:
            self.assertFalse(self.raw(json.dumps({**valid, key: value}).encode())[1]["ok"])
        self.assertFalse(self.raw(b'{"protocol":"rule-case-workbench/1","action":"open","action":"run"}')[1]["ok"])
        self.assertEqual(self.raw(json.dumps(valid).encode(), path="/api")[0], 404)
        self.assertEqual(self.raw(b"{}", headers={"Content-Type": "application/json", "Origin": "http://foreign.example"})[0], 403)
        self.assertIsNone(self.adapter.active)

    def test_cancel_before_run_and_used_run_id_cannot_revive(self):
        self.assertEqual(self.post("cancel", sessionId=self.session, runId="late")[0], 200)
        self.assertEqual(self.run_case(run_id="late")[1]["code"], "RETIRED")
        self.assertEqual(self.run_case(run_id="once")[0], 200)
        self.assertEqual(self.run_case(run_id="once")[1]["code"], "RETIRED")

    def held_child(self, action):
        entered, release = threading.Event(), threading.Event()
        originals = _Child.command
        observed, returned = {}, []

        def held(child, command):
            if not observed:
                observed.update(pid=child.process.pid, directory=Path(child.process.args[0]).parent)
                entered.set()
                if not release.wait(5):
                    raise AssertionError("test lifecycle gate timed out")
            return originals(child, command)

        with patch.object(_Child, "command", held):
            worker = threading.Thread(target=lambda: returned.append(self.run_case(run_id="held")))
            worker.start()
            self.assertTrue(entered.wait(5))
            try:
                action()
            finally:
                release.set(); worker.join(10)
            self.assertFalse(worker.is_alive())
        self.assertFalse(observed["directory"].exists())
        if os.name != "nt":
            with self.assertRaises(ProcessLookupError):
                os.kill(observed["pid"], 0)
        self.assertEqual(returned[0][0], 409, returned)
        self.assertEqual(returned[0][1]["code"], "RETIRED")
        self.assertNotIn("receipt", returned[0][1])

    def test_cancel_during_real_native_child_discards_late_receipt_and_reaps(self):
        self.held_child(lambda: self.post("cancel", sessionId=self.session, runId="held"))
        self.assertEqual(self.run_case(run_id="next")[0], 200)

    def test_close_reopen_during_real_native_child_does_not_revive_old_run(self):
        def action():
            self.post("close", sessionId=self.session)
            new = self.post("open")[1]["sessionId"]
            self.assertNotEqual(new, self.session)
        self.held_child(action)

    def test_project_generation_undo_and_reopen_fence_original_scope(self):
        for key, value in [("projectId", "project-B"), ("generation", 8), ("contextToken", "undo-even-same-data")]:
            self.context = {"projectId": "http-workbench-project", "generation": 7,
                            "contextToken": "original-http-context"}
            self.session = self.post("open")[1]["sessionId"]
            self.held_child(lambda: self.context.update({key: value}))

    def test_serial_concurrency_gate_leaves_other_run_and_candidate_isolated(self):
        def action():
            status, result = self.run_case(run_id="second")
            self.assertEqual((status, result["code"]), (409, "BUSY"))
            self.post("cancel", sessionId=self.session, runId="held")
        self.held_child(action)

    def test_timeout_output_unknown_runtime_and_capability_are_nonpass(self):
        for settings, expected in [({"timeout_seconds": .01}, "timeout"),
                                   ({"max_output_bytes": 1}, "blocked"),
                                   ({"binary": "/unavailable-workbench-binary"}, "unknown-runtime")]:
            adapter = RuleCaseWorkbenchAdapter(capture_context=lambda: self.context,
                                                **{"binary": self.binary, **settings})
            _, opened = adapter.dispatch("POST", "/rule-cases/workbench", json.dumps({"protocol": PROTOCOL, "action": "open"}).encode())
            payload = {"protocol": PROTOCOL, "action": "run", "sessionId": opened["sessionId"],
                       "runId": "limits", "definition": case("legal-rule")}
            _, result = adapter.dispatch("POST", "/rule-cases/workbench", json.dumps(payload).encode())
            self.assertEqual(result["receipt"]["status"], expected, result)
            self.assertTrue(result["receipt"]["conditions"]["privateDirectoryRemoved"])
            adapter.close()
        definition = case("legal-rule")
        definition["requiredCapabilities"].append("absent-workbench/1")
        _, result = self.run_case(definition=definition)
        self.assertEqual(result["receipt"]["status"], "missing-capability")
        self.assert_reaped(result["receipt"])


if __name__ == "__main__":
    unittest.main()
