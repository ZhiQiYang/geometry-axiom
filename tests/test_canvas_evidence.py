"""Pure raw/provenance controls for the canvas receipt supervisor; no browser."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("canvas_evidence", ROOT / ".github/scripts/canvas_evidence.py")
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


class CanvasEvidence(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="canvas-receipt-control-")
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.expected = {"execution_sha": "a" * 40, "head_sha": "b" * 40, "tree": "c" * 40,
                         "run_id": "123", "run_attempt": "1", "runtime_version": "e" * 64}
        self.plan = {"sha256": "d" * 64}
        self.result = {"schema": "geometry-cdp-result/1", "scope": {"mode": "shard", "url": "http://127.0.0.1:18839/",
                       "feedbackDirectory": "/tmp/canvas-pure-feedback"}, "sections": {"Setup": 0}, "passedAssertions": 0}
        (self.folder / "plan.json").write_text(json.dumps(self.plan))
        (self.folder / "runtime.stdout").write_text(json.dumps({"schema": "geometry-runtime/1", "fresh": True,
            "root": "/ci/source", "version": self.expected["runtime_version"]}))
        (self.folder / "runtime.stderr").write_text("")
        (self.folder / "stdout.log").write_text("CDP_RESULT " + json.dumps(self.result) + "\n")
        (self.folder / "stderr.log").write_text("")
        self.receipt = {"schema": "geometry-canvas-shard/1", **self.expected, "shard": "legacy", "verified": True,
                        "process_exit": 0, "runtime_exit": 0, "command": ["node", "geometry-web/cdp_test.js"],
                        "runtime_command": ["<python>", "-B", "geometry-web/runtime_version.py", "--probe", "18839"],
                        "execution_root": "/ci/source", "runtime_version": self.expected["runtime_version"],
                        "environment": {"GEOMETRY_CDP_SHARD": "legacy", "GEOMETRY_TEST_URL": "http://127.0.0.1:18839/",
                                        "GEOMETRY_FEEDBACK_DIR": "/tmp/canvas-pure-feedback"},
                        "plan_sha256": self.plan["sha256"], "scope": self.result["scope"], "sections": self.result["sections"],
                        "assertions": 0, "files": {name: evidence.sha(self.folder / name) for name in evidence.FILES}}

    def verify(self, receipt=None):
        return evidence.verify_manifest(receipt or self.receipt, self.expected, self.plan, self.folder)

    def test_real_original_bytes_are_read_before_trace_verification(self):
        self.assertEqual(self.verify()["id"], "legacy")

    def test_canvas_wrong_head_rejects_execution_head_pr_head_and_tree(self):
        for field in ("execution_sha", "head_sha", "tree"):
            with self.subTest(field=field):
                receipt = deepcopy(self.receipt)
                receipt[field] = "e" * 40
                with self.assertRaisesRegex(ValueError, "CANVAS_WRONG_HEAD: " + field):
                    self.verify(receipt)

    def test_canvas_wrong_run_attempt_rejects_same_head_foreign_receipts(self):
        for field in ("run_id", "run_attempt"):
            with self.subTest(field=field):
                receipt = deepcopy(self.receipt)
                receipt[field] = "2"
                with self.assertRaisesRegex(ValueError, "CANVAS_WRONG_RUN_ATTEMPT: " + field):
                    self.verify(receipt)

    def test_duplicate_json_keys_and_truncated_raw_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "CANVAS_DUPLICATE_JSON_KEY"):
            evidence.read_json('{"completed":false,"completed":true}')
        with self.assertRaises(json.JSONDecodeError):
            evidence.trace(b'CDP_RESULT {"completed":tr')

    def test_second_completed_result_cannot_replace_an_earlier_failure(self):
        with self.assertRaisesRegex(ValueError, "CANVAS_RESULT_COUNT"):
            evidence.trace(b'CDP_RESULT {"completed":false}\nCDP_RESULT {"completed":true}\n')

    def test_raw_corruption_and_resigned_changed_plan_are_rejected(self):
        (self.folder / "stderr.log").write_text("changed raw")
        with self.assertRaisesRegex(ValueError, "CANVAS_RAW_CHANGED: stderr.log"):
            self.verify()
        self.receipt["files"]["stderr.log"] = evidence.sha(self.folder / "stderr.log")
        (self.folder / "plan.json").write_text(json.dumps({"sha256": "e" * 64}))
        self.receipt["files"]["plan.json"] = evidence.sha(self.folder / "plan.json")
        with self.assertRaisesRegex(ValueError, "CANVAS_SOURCE_OR_GOLDEN_CHANGED"):
            self.verify()

    def test_actual_parent_exit_cannot_be_boolean_or_nonzero(self):
        for value in (True, 1, 2):
            receipt = deepcopy(self.receipt)
            receipt["process_exit"] = value
            with self.assertRaisesRegex(ValueError, "CANVAS_PROCESS_FAILED"):
                self.verify(receipt)

    def test_runtime_not_fresh_is_rejected_even_with_updated_hash(self):
        (self.folder / "runtime.stdout").write_text(json.dumps({"schema": "geometry-runtime/1", "fresh": False}))
        self.receipt["files"]["runtime.stdout"] = evidence.sha(self.folder / "runtime.stdout")
        with self.assertRaisesRegex(ValueError, "CANVAS_RUNTIME_NOT_FRESH"):
            self.verify()

    def test_runtime_must_be_the_actual_browser_loopback_service_and_original_probe(self):
        receipt = deepcopy(self.receipt)
        receipt["environment"]["GEOMETRY_TEST_URL"] = "http://example.com:18839/"
        with self.assertRaisesRegex(ValueError, "CANVAS_RUNTIME_ENDPOINT"):
            self.verify(receipt)
        receipt = deepcopy(self.receipt)
        receipt["runtime_command"][-1] = "18840"
        with self.assertRaisesRegex(ValueError, "CANVAS_RUNTIME_COMMAND_CHANGED"):
            self.verify(receipt)
        receipt = deepcopy(self.receipt)
        receipt["execution_root"] = "/other/source"
        with self.assertRaisesRegex(ValueError, "CANVAS_RUNTIME_SOURCE_CHANGED"):
            self.verify(receipt)

    def test_browser_url_and_result_schema_cannot_be_changed_with_resigned_raw(self):
        for field, value, code in (("schema", "other", "CANVAS_RESULT_SCHEMA"),
                                   ("scope", {**self.result["scope"], "url": "http://127.0.0.1:18840/"}, "CANVAS_RUNTIME_SCOPE_CHANGED")):
            with self.subTest(field=field):
                result = {**self.result, field: value}
                (self.folder / "stdout.log").write_text("CDP_RESULT " + json.dumps(result) + "\n")
                self.receipt["files"]["stdout.log"] = evidence.sha(self.folder / "stdout.log")
                with self.assertRaisesRegex(ValueError, code):
                    self.verify()

    def test_shallow_merge_parent_binding_reads_the_original_commit_object(self):
        def fake_git(*args):
            if args == ("status", "--porcelain=v1"):
                return ""
            if args == ("rev-parse", "HEAD"):
                return "a" * 40
            if args == ("cat-file", "-p", "a" * 40):
                return "tree " + "c" * 40 + "\nparent " + "b" * 40 + "\n"
            if args == ("rev-parse", "HEAD^{tree}"):
                return "c" * 40
            self.fail("Unexpected Git parent traversal: " + repr(args))
        with patch.object(evidence, "git", side_effect=fake_git), patch.dict(evidence.os.environ,
                {"EXPECTED_EXECUTION_SHA": "a" * 40, "PR_HEAD_SHA": "b" * 40}):
            self.assertEqual(evidence.source_identity()["head_sha"], "b" * 40)

    def test_commit_message_cannot_forge_a_pr_parent(self):
        def fake_git(*args):
            if args == ("status", "--porcelain=v1"):
                return ""
            if args == ("rev-parse", "HEAD"):
                return "a" * 40
            if args == ("cat-file", "-p", "a" * 40):
                return "tree " + "c" * 40 + "\nparent " + "d" * 40 + "\n\nmessage\nparent " + "b" * 40 + "\n"
            self.fail("Unexpected Git operation: " + repr(args))
        with patch.object(evidence, "git", side_effect=fake_git), patch.dict(evidence.os.environ,
                {"EXPECTED_EXECUTION_SHA": "a" * 40, "PR_HEAD_SHA": "b" * 40}):
            with self.assertRaisesRegex(ValueError, "CANVAS_WRONG_PR_HEAD"):
                evidence.source_identity()


if __name__ == "__main__":
    unittest.main()
