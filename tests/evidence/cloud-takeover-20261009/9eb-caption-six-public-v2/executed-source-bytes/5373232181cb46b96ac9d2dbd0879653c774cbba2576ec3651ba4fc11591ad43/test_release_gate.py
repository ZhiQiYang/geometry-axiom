#!/usr/bin/env python3
"""Negative evidence tests for release_gate's command receipts and identity checks."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import release_gate as gate


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="geometry-release-selftest-")
        self.base = Path(self.temp.name)
        self.root = self.base / "repo"
        (self.root / "geometry-web").mkdir(parents=True)
        self.output = self.base / "evidence"
        self.url = "http://127.0.0.1:18970/"
        self.good = {
            "root": str(self.root), "problems": [],
            "git": {"root": str(self.root), "head": "abc", "tree": "def", "status": ""},
            "sourceVersion": "source1", "native": {"bridge": {"state": "fresh", "sha256": "a"}},
            "runtime": {"schema": "geometry-runtime/1", "root": str(self.root), "version": "source1",
                        "session": "session1", "pid": 10, "fresh": True}}
        self.cdp = {"schema": "geometry-cdp-result/1", "completed": True,
                    "scope": {"mode": "full", "filters": [], "modifiers": [], "url": self.url},
                    "passedAssertions": 2, "failedAssertions": 0, "skipped": [],
                    "sections": {"Setup": 0, "P1": 2}, "goldenCompare": "matched"}
        (self.root / "geometry-web/cdp_sections.golden.json").write_text(json.dumps(
            {"sections": self.cdp["sections"], "total": 2}), encoding="utf-8")
        (self.root / "geometry-web/space_test_floor.js").write_text(
            "module.exports={EXPECTED:{setup:2,a:3,b:4,'browser-health':2},FULL_SPACE_GROUPS:['a','b']}",
            encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def run_fake(self, before=None, after=None, row=None, execution=None, command=None):
        captures = iter([copy.deepcopy(before or self.good), copy.deepcopy(after or self.good)])
        called = []
        def runner(command, root, env, log, timeout):
            called.append(command)
            Path(log).write_text("full stdout\nfull stderr\n" + ("CDP_RESULT " + json.dumps(row) + "\n" if row is not None else ""), encoding="utf-8")
            return execution or {"exitCode": 0, "timedOut": False, "interrupted": False}
        code, receipt = gate.run_gate(self.root, self.url, self.output,
                                     command or [sys.executable, "unknown.py"], {}, 10,
                                     capture=lambda *a: next(captures), runner=runner)
        persisted = json.loads((self.output / "receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt, persisted)
        self.assertFalse(receipt["releaseApproved"])
        self.assertEqual(receipt["log"]["sha256"], gate.sha(self.output / "command.log"))
        return code, receipt, called

    def test_arbitrary_exit_zero_only_verifies_command_execution(self):
        code, result, _ = self.run_fake()
        self.assertEqual(code, 0)
        self.assertTrue(result["executionVerified"])
        self.assertFalse(result["evidence"]["completionVerified"])
        self.assertEqual(result["evidence"]["scope"], "command-only")

    def test_preflight_rejection_does_not_execute_and_still_retains_receipt(self):
        before = copy.deepcopy(self.good)
        before["problems"] = ["dirty checkout"]
        code, result, calls = self.run_fake(before=before)
        self.assertEqual(code, 2)
        self.assertFalse(calls)
        self.assertFalse(result["executionVerified"])
        self.assertEqual(result["log"]["bytes"], 0)

    def test_identity_drift_rejects_successful_exit(self):
        for key, field, value in (("git", "head", "new"), ("git", "tree", "new"),
                                  ("git", "status", " M app.js"), ("runtime", "session", "new"),
                                  ("runtime", "pid", 11), ("runtime", "root", "/other"),
                                  ("runtime", "version", "new")):
            with self.subTest(key=key, field=field):
                self.output = self.base / (key + "-" + field)
                after = copy.deepcopy(self.good)
                after[key][field] = value
                code, result, _ = self.run_fake(after=after)
                self.assertNotEqual(code, 0)
                self.assertFalse(result["executionVerified"])

    def test_source_and_native_changes_reject_successful_exit(self):
        for key, value in (("sourceVersion", "new"), ("native", {})):
            with self.subTest(key=key):
                self.output = self.base / key
                after = copy.deepcopy(self.good)
                after[key] = value
                self.assertNotEqual(self.run_fake(after=after)[0], 0)

    def test_after_staleness_rejects_successful_exit(self):
        after = copy.deepcopy(self.good)
        after["problems"] = ["runtime no longer fresh"]
        self.assertNotEqual(self.run_fake(after=after)[0], 0)

    def test_failed_command_retains_log_and_after_identity(self):
        code, result, _ = self.run_fake(execution={"exitCode": 7})
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "command-failed")
        self.assertIn("after", result)
        self.assertIn("full stderr", (self.output / "command.log").read_text())

    def test_interrupted_and_timeout_are_not_success(self):
        for field, code in (("interrupted", 130), ("timedOut", 124)):
            with self.subTest(field=field):
                self.output = self.base / field
                actual, result, _ = self.run_fake(execution={"exitCode": 0, field: True})
                self.assertEqual(actual, code)
                self.assertFalse(result["executionVerified"])

    def test_existing_evidence_is_never_overwritten(self):
        self.output.mkdir()
        marker = self.output / "receipt.json"
        marker.write_bytes(b"previous evidence")
        with self.assertRaises(FileExistsError):
            self.run_fake()
        self.assertEqual(marker.read_bytes(), b"previous evidence")

    def test_output_inside_checkout_is_rejected(self):
        self.output = self.root / "evidence"
        with self.assertRaises(ValueError):
            self.run_fake()
        self.assertFalse(self.output.exists())

    def test_missing_canonical_result_cannot_succeed(self):
        code, result, _ = self.run_fake(command=["node", "geometry-web/cdp_test.js"])
        self.assertNotEqual(code, 0)
        self.assertIn("canonical result", " ".join(result["problems"]))

    def test_complete_cdp_requires_committed_census(self):
        code, result, _ = self.run_fake(row=self.cdp, command=["node", "geometry-web/cdp_test.js"])
        self.assertEqual(code, 0)
        self.assertTrue(result["evidence"]["completionVerified"])
        self.assertEqual(result["evidence"]["scope"]["mode"], "full")

    def test_incomplete_failed_skipped_or_miscounted_cdp_rejects_exit_zero(self):
        for key, value in (("completed", False), ("failedAssertions", 1), ("passedAssertions", 0),
                           ("sections", {"P1": 1}), ("goldenCompare", "not compared"),
                           ("skipped", ["P1"]), ("schema", "unknown")):
            with self.subTest(key=key):
                self.output = self.base / key
                row = copy.deepcopy(self.cdp)
                row[key] = value
                self.assertNotEqual(self.run_fake(row=row, command=["node", "geometry-web/cdp_test.js"])[0], 0)

    def test_partial_cdp_preserves_partial_scope(self):
        row = copy.deepcopy(self.cdp)
        row["scope"] = {"mode": "partial", "filters": ["GEOMETRY_ASSEMBLY_ONLY"], "modifiers": [], "url": self.url}
        row["goldenCompare"] = "partial"
        code, result, _ = self.run_fake(row=row, command=["node", "geometry-web/cdp_test.js"])
        self.assertEqual(code, 0)
        self.assertEqual(result["evidence"]["scope"]["mode"], "partial")
        self.assertFalse(result["releaseApproved"])

    def test_canonical_command_cannot_switch_to_a_different_service(self):
        row = copy.deepcopy(self.cdp)
        row["scope"]["url"] = "http://127.0.0.1:8765/"
        code, result, _ = self.run_fake(row=row, command=["node", "geometry-web/cdp_test.js"])
        self.assertNotEqual(code, 0)
        self.assertIn("canonical command used a different service URL", result["problems"])

    def test_duplicate_and_malformed_canonical_results_rejected(self):
        for content in ("CDP_RESULT {}\nCDP_RESULT {}\n", "CDP_RESULT invalid\n"):
            with self.subTest(content=content):
                path = self.base / "probe.log"
                path.write_text(content)
                self.assertTrue(gate.inspect_result(path, "cdp", self.root)[1])

    def test_full_space_cannot_omit_a_group_or_lower_its_floor(self):
        row = {"schema": "geometry-space-result/1", "completed": True, "passed": 7, "failed": 0,
               "scope": {"mode": "full-space-suite", "filters": [], "included": ["a"]},
               "exceptions": [], "consoleErrors": [], "completenessProblems": [],
               "groups": {name: {"expected": n, "passed": n, "failed": 0, "completed": True}
                          for name, n in (("setup", 2), ("a", 3), ("browser-health", 2))}}
        path = self.base / "space.log"
        path.write_text("SPACE_RESULT " + json.dumps(row))
        self.assertTrue(gate.inspect_result(path, "space", self.root)[1])
        row["scope"].update(mode="partial", filters=["GEOMETRY_SPACE_FLOW_ONLY"])
        row["groups"]["a"].update(expected=1, passed=1)
        row["passed"] = 5
        path.write_text("SPACE_RESULT " + json.dumps(row))
        self.assertTrue(gate.inspect_result(path, "space", self.root)[1])

    def test_real_process_failure_records_stdout_stderr_and_exit(self):
        result = gate.execute([sys.executable, "-c", "import sys; print('stdout'); print('stderr',file=sys.stderr);sys.exit(9)"],
                              self.root, dict(os.environ), self.base / "process.log", 5)
        self.assertEqual(result["exitCode"], 9)
        content = (self.base / "process.log").read_text()
        self.assertIn("stdout", content)
        self.assertIn("stderr", content)

    def test_real_timeout_retains_output_and_stops_owned_process(self):
        result = gate.execute([sys.executable, "-u", "-c", "import time;print('before timeout',flush=True);time.sleep(30)"],
                              self.root, dict(os.environ), self.base / "timeout.log", 0.2)
        self.assertTrue(result["timedOut"])
        self.assertIsNotNone(result["exitCode"])
        self.assertIn("before timeout", (self.base / "timeout.log").read_text())

    def test_runtime_preflight_rejects_wrong_root_stale_and_wrong_source(self):
        native = SimpleNamespace(BY_NAME={"bridge": 1, "model-base": 2})
        runtime = SimpleNamespace(source_version=lambda root: "source1")
        def fake_module(path, name):
            return runtime if name == "release_runtime" else native
        def fake_git(root, *args):
            return str(self.root) if args == ("rev-parse", "--show-toplevel") else "" if args[0] == "status" else "sha"
        for key, value in (("root", "/wrong"), ("fresh", False), ("version", "wrong"), ("session", ""), ("pid", 0)):
            with self.subTest(key=key), patch.object(gate, "module", fake_module), patch.object(gate, "git", fake_git):
                observed = copy.deepcopy(self.good["runtime"])
                observed[key] = value
                with patch.object(gate, "runtime_status", return_value=observed):
                    snapshot = gate.snapshot(self.root, self.url, {})
                    self.assertIn("runtime schema/root/source/fresh/session/pid mismatch", snapshot["problems"])

    def test_native_preflight_requires_fresh_sidecars(self):
        runtime = SimpleNamespace(source_version=lambda root: "source1")
        info = SimpleNamespace(state="stale", reason="source fingerprint differs", fingerprint="old",
                               as_dict=lambda: {"state": "stale", "path": "/native"})
        native = SimpleNamespace(BY_NAME={"bridge": 1, "model-base": 2}, inspect_one=lambda *a, **kw: info)
        with patch.object(gate, "module", side_effect=[runtime, native]), \
                patch.object(gate, "runtime_status", return_value=self.good["runtime"]), \
                patch.object(gate, "git", return_value=str(self.root)):
            result = gate.snapshot(self.root, self.url, {"GEOMETRY_TEST_BRIDGE": "/b", "GEOMETRY_MODEL_BASE": "/m"})
        self.assertTrue(any("bridge native is not fresh" in item for item in result["problems"]))
        self.assertTrue(any("model-base native is not fresh" in item for item in result["problems"]))

    def test_urls_cannot_point_at_external_services_or_include_credentials(self):
        for value in ("https://example.com/", "http://user:pass@localhost:9/", "http://localhost:9/path",
                      "http://localhost/", "http://localhost:9/?q=1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                gate.normalize_url(value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
