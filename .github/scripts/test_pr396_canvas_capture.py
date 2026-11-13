"""Synthetic envelope guards only; never a browser acceptance receipt."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

SCRIPT = Path(__file__).with_name("pr396_canvas_capture.py")


class CaptureEnvelope(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "R396_CAPTURE_COLLECTOR_REQUIRED")
        spec = importlib.util.spec_from_file_location("pr396_capture_under_test", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.temporary = tempfile.TemporaryDirectory(prefix="pr396-capture-envelope-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.folder = self.root / "pr396-capture-2"
        self.folder.mkdir()
        self.expected = {"execution_sha": "a" * 40, "head_sha": "b" * 40, "tree": "c" * 40,
                         "run_id": "123", "run_attempt": "1"}
        self.closure = {"version": "d" * 64, "files": {"geometry-web/app.js": "e" * 64}}
        self.plan = {"schema": "geometry-canvas-capture-plan/1", "acceptance": False,
                     "shards": ["1/2", "2/2"], "sha256": "f" * 64}
        self.environment = {"GEOMETRY_TEST_URL": "http://127.0.0.1:18839/", "GEOMETRY_FEEDBACK_DIR": "/tmp/capture-fb",
                            "GEOMETRY_CHROME": "/usr/bin/google-chrome", "GEOMETRY_CHROME_FLAGS": "--no-sandbox",
                            "GEOMETRY_CDP_PORT": "9333", "GEOMETRY_CDP_SHARD": "2/2", "GEOMETRY_CDP_CAPTURE_P1161": "1",
                            "GEOMETRY_GRID_SYSTEM_SCREENSHOT_DIR": "/tmp/geometry-grid-screens",
                            "GEOMETRY_DOCUMENT_SCREENSHOT_DIR": "/tmp/geometry-document-screens"}
        self.scope = {"mode": "capture-shard", "acceptance": False, "filters": [], "modifiers": [],
                      "shard": {"index": 2, "count": 2}, "url": self.environment["GEOMETRY_TEST_URL"],
                      "feedbackDirectory": self.environment["GEOMETRY_FEEDBACK_DIR"]}
        self.result = {"schema": "geometry-cdp-result/1", "scope": self.scope, "completed": True,
                       "sections": {"P1161": 12}, "passedAssertions": 12, "elapsedSeconds": 600}
        self.runtime = {"schema": "geometry-runtime/1", "fresh": True, "root": "/tmp/runtime-source", "version": self.closure["version"]}
        self.receipt = {"schema": "geometry-canvas-capture-shard/1", "acceptance": False,
                        "capture_verified": True, **self.expected, "shard": "2/2", "command": self.m.COMMAND,
                        "runtime_command": ["<python>", "-B", "geometry-web/runtime_version.py", "--probe", "18839"],
                        "runtime_exit": 0, "process_exit": 0, "plan_sha256": self.plan["sha256"],
                        "execution_root": self.runtime["root"], "runtime_version": self.runtime["version"],
                        "environment": self.environment, "scope": self.scope,
                        "sections": self.result["sections"], "assertions": self.result["passedAssertions"], "files": {}}
        for name, value in (("plan.json", self.plan), ("source.json", self.closure), ("runtime.stdout", self.runtime)):
            self.write_json(name, value)
        for name in ("runtime.stderr", "stderr.log"):
            self.write_raw(name, b"")
        self.write_trace()

    def write_raw(self, name, raw):
        (self.folder / name).write_bytes(raw)
        self.receipt["files"][name] = hashlib.sha256(raw).hexdigest()

    def write_json(self, name, value):
        self.write_raw(name, (json.dumps(value) + "\n").encode())

    def write_trace(self, scope=None, result=None, extra=""):
        scope = self.scope if scope is None else scope
        result = self.result if result is None else result
        self.write_raw("stdout.log", ("CDP_SCOPE " + json.dumps(scope) + "\nCDP_RESULT " + json.dumps(result) + "\n" + extra).encode())

    def verify(self, receipt=None):
        # Runtime endpoint parsing is the existing strict official helper;
        # this unit isolates the new raw/source/identity envelope from the JS
        # journal judge, which has separate full-sequence adversarial tests.
        with mock.patch.object(self.m, "runtime_endpoint", return_value=18839):
            return self.m.verify_manifest(self.receipt if receipt is None else receipt,
                                          self.expected, self.closure, self.plan, self.folder)

    def reject(self, marker, receipt=None):
        with self.assertRaisesRegex(ValueError, marker):
            self.verify(receipt)

    def test_exact_synthetic_envelope_reaches_the_independent_journal_judge(self):
        value = self.verify()
        self.assertEqual(value["id"], "2/2")
        self.assertEqual(value["scope"], self.scope)
        self.assertEqual(value["result"], self.result)
        self.assertEqual(value["events"], [])
        self.assertIs(value["scope"]["acceptance"], False)

    def test_all_five_source_and_run_fields_are_exact(self):
        for field in self.expected:
            with self.subTest(field=field):
                bad = copy.deepcopy(self.receipt)
                bad[field] += "0"
                self.reject("CAPTURE_IDENTITY_CHANGED:" + field, bad)

    def test_capture_cannot_impersonate_strict_acceptance(self):
        for change in ({"schema": "geometry-canvas-shard/1"}, {"acceptance": True}, {"acceptance": None}):
            with self.subTest(change=change):
                self.reject("CAPTURE_RECEIPT_SCHEMA", {**self.receipt, **change})

    def test_both_real_exit_codes_are_integer_zero(self):
        for field in ("runtime_exit", "process_exit"):
            for value in (False, None, "0", 1, -15):
                with self.subTest(field=field, value=value):
                    self.reject("CAPTURE_PROCESS_FAILED", {**self.receipt, field: value})

    def test_failed_capture_flag_cannot_be_repaired_by_zero_exit(self):
        self.reject("CAPTURE_PROCESS_FAILED", {**self.receipt, "capture_verified": False})

    def test_execution_command_is_exact(self):
        self.reject("CAPTURE_COMMAND_CHANGED", {**self.receipt, "command": ["node", "geometry-web/cdp_test.js", "--skip"]})
        self.reject("CAPTURE_RUNTIME_COMMAND_CHANGED", {**self.receipt, "runtime_command": ["true"]})

    def test_scope_environment_cannot_change_partition_or_mode(self):
        for key, value in (("GEOMETRY_CDP_SHARD", "1/2"), ("GEOMETRY_CDP_CAPTURE_P1161", "0")):
            with self.subTest(key=key):
                bad = copy.deepcopy(self.receipt)
                bad["environment"][key] = value
                self.reject("CAPTURE_SCOPE_CHANGED", bad)

    def test_no_missing_or_extra_raw_files(self):
        for name in self.m.FILES:
            with self.subTest(missing=name):
                bad = copy.deepcopy(self.receipt)
                bad["files"].pop(name)
                self.reject("CAPTURE_MISSING_RAW", bad)
        bad = copy.deepcopy(self.receipt)
        bad["files"]["ignored.log"] = "a" * 64
        self.reject("CAPTURE_MISSING_RAW", bad)

    def test_raw_hash_detects_even_semantically_neutral_rewrite(self):
        with (self.folder / "stdout.log").open("ab") as stream:
            stream.write(b"\n")
        self.reject("CAPTURE_RAW_CHANGED:stdout.log")

    def test_symlink_cannot_replace_a_raw_receipt(self):
        path = self.folder / "stderr.log"
        other = self.root / "outside.log"
        other.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(other)
        self.reject("CAPTURE_RAW_CHANGED:stderr.log")

    def test_plan_hash_and_bytes_both_bind_the_source(self):
        self.reject("CAPTURE_PLAN_CHANGED", {**self.receipt, "plan_sha256": "0" * 64})
        changed = {**self.plan, "extra": "unreviewed"}
        self.write_json("plan.json", changed)
        self.reject("CAPTURE_PLAN_CHANGED")

    def test_rehashed_source_closure_cannot_change_a_product_file(self):
        changed = copy.deepcopy(self.closure)
        changed["files"]["geometry-web/app.js"] = "0" * 64
        self.write_json("source.json", changed)
        self.reject("CAPTURE_SOURCE_CHANGED")

    def test_runtime_must_be_fresh_and_match_actual_checkout(self):
        self.write_json("runtime.stdout", {**self.runtime, "fresh": False})
        self.reject("CAPTURE_RUNTIME_NOT_FRESH")
        self.write_json("runtime.stdout", {**self.runtime, "root": "/tmp/wrong-source"})
        self.reject("CAPTURE_RUNTIME_SOURCE_CHANGED")
        changed = {**self.runtime, "version": "0" * 64}
        self.write_json("runtime.stdout", changed)
        self.reject("CAPTURE_RUNTIME_SOURCE_CHANGED", {**self.receipt, "runtime_version": changed["version"]})

    def test_runtime_url_and_feedback_directory_bind_both_raw_scopes(self):
        for key, value in (("url", "http://127.0.0.1:19000/"), ("feedbackDirectory", "/tmp/other-feedback")):
            with self.subTest(key=key):
                scope = {**self.scope, key: value}
                result = {**self.result, "scope": scope}
                self.write_trace(scope, result)
                self.reject("CAPTURE_RUNTIME_SCOPE_CHANGED", {**self.receipt, "scope": scope})

    def test_result_elapsed_time_never_relaxes_the_original_cap(self):
        for value in (False, None, "600", -1, 2100, 2101):
            with self.subTest(value=value):
                self.write_trace(result={**self.result, "elapsedSeconds": value})
                self.reject("CAPTURE_35_MINUTE_LIMIT")

    def test_scope_must_be_explicitly_nonacceptance_capture(self):
        for change in ({"mode": "full"}, {"mode": "shard"}, {"acceptance": True}):
            with self.subTest(change=change):
                scope = {**self.scope, **change}
                self.write_trace(scope, {**self.result, "scope": scope})
                self.reject("CAPTURE_SCOPE_CHANGED", {**self.receipt, "scope": scope})

    def test_receipt_summary_cannot_override_raw_result(self):
        self.reject("CAPTURE_FAKE_SUMMARY", {**self.receipt, "assertions": 13})
        self.reject("CAPTURE_FAKE_SUMMARY", {**self.receipt, "sections": {"P1161": 13}})

    def test_duplicate_scope_result_and_json_keys_are_rejected(self):
        for prefix, value in (("CDP_SCOPE ", self.scope), ("CDP_RESULT ", self.result)):
            with self.subTest(prefix=prefix):
                self.write_trace(extra=prefix + json.dumps(value) + "\n")
                self.reject("CAPTURE_ONE_SCOPE_AND_RESULT")
        self.write_raw("stdout.log", b'CDP_SCOPE {"mode":"full","mode":"capture-shard"}\n')
        self.reject("CAPTURE_DUPLICATE_JSON_KEY")

    def test_wrong_folder_is_not_silently_matched_by_content(self):
        self.folder = self.folder.rename(self.root / "pr396-capture-1")
        self.reject("CAPTURE_SHARD_DIRECTORY")

    def test_environment_drops_unrelated_geometry_flags(self):
        inherited = {**self.environment, "GEOMETRY_UNKNOWN_TIMEOUT": "90000", "PATH": "/usr/bin"}
        with mock.patch.dict(os.environ, inherited, clear=True):
            env = self.m.capture_environment("2/2")
        self.assertNotIn("GEOMETRY_UNKNOWN_TIMEOUT", env)
        self.assertEqual(env["PATH"], "/usr/bin")
        self.assertEqual(env["GEOMETRY_CDP_SHARD"], "2/2")
        self.assertEqual(env["GEOMETRY_CDP_CAPTURE_P1161"], "1")
        self.assertEqual(env["GEOMETRY_GRID_SYSTEM_SCREENSHOT_DIR"], "/tmp/geometry-grid-screens")
        self.assertEqual(env["GEOMETRY_DOCUMENT_SCREENSHOT_DIR"], "/tmp/geometry-document-screens")

    def test_environment_rejects_partial_filter_and_golden_update(self):
        for key in ("GEOMETRY_GRID_SYSTEM_ONLY", "GEOMETRY_WORKSPACE_CONTEXT_MENU_CASES", "GEOMETRY_GRID_CARD_ENTRY_CASE", "GEOMETRY_CDP_UPDATE_GOLDEN"):
            with self.subTest(key=key), mock.patch.dict(os.environ, {**self.environment, key: "1"}, clear=True):
                with self.assertRaisesRegex(ValueError, "CAPTURE_INHERITED_SCOPE"):
                    self.m.capture_environment("2/2")

    def test_environment_rejects_a_different_inherited_partition(self):
        with mock.patch.dict(os.environ, self.environment, clear=True):
            with self.assertRaisesRegex(ValueError, "CAPTURE_INHERITED_SHARD"):
                self.m.capture_environment("1/2")

    def test_formal_browser_path_and_flags_are_fixed(self):
        for key, value in (("GEOMETRY_CHROME", "/tmp/other-chrome"), ("GEOMETRY_CHROME_FLAGS", "--no-sandbox --disable-web-security")):
            with self.subTest(key=key):
                changed = {**self.environment, key: value}
                with mock.patch.dict(os.environ, changed, clear=True):
                    with self.assertRaisesRegex(ValueError, "CAPTURE_BROWSER_CONFIG_CHANGED"):
                        self.m.capture_environment("2/2")
                self.reject("CAPTURE_BROWSER_CONFIG_CHANGED", {**self.receipt, "environment": changed})
        for key in self.m.SCREENSHOT_ENV:
            with self.subTest(screenshot=key):
                changed = {**self.environment, key: "/tmp/changed-screens"}
                with mock.patch.dict(os.environ, changed, clear=True):
                    with self.assertRaisesRegex(ValueError, "CAPTURE_SCREENSHOT_CONFIG_CHANGED"):
                        self.m.capture_environment("2/2")
                self.reject("CAPTURE_SCREENSHOT_CONFIG_CHANGED", {**self.receipt, "environment": changed})

    def test_unverified_generator_is_never_imported(self):
        path = self.root / "PR396-complete-canvas.py"
        path.write_text("raise RuntimeError('must never execute')\n")
        path.with_name("PR396-canvas-T.patch").write_text("also wrong\n")
        with mock.patch.object(self.m, "load_module") as imported:
            with self.assertRaisesRegex(ValueError, "CAPTURE_GENERATOR_CHANGED"):
                self.m.generator(path)
            imported.assert_not_called()

    def test_candidate_comment_describes_capture_provenance_honestly(self):
        old = b"// Its exact count was captured from one full, zero-failure cdp_test.js run.\n"
        tool = SimpleNamespace(TEST="test.js", render_after=lambda *_: {"test.js": old, "golden.json": b"old golden bytes"})
        after = self.m.candidate_sources(tool, {}, b"", 12)
        self.assertNotIn(b"one full", after["test.js"])
        self.assertIn(b"two complete capture partitions", after["test.js"])
        self.assertEqual(after["golden.json"], b"old golden bytes")
        tool.render_after = lambda *_: {"test.js": b"unexpected original renderer output"}
        with self.assertRaisesRegex(ValueError, "CAPTURE_PROVENANCE_ANCHOR"):
            self.m.candidate_sources(tool, {}, b"", 12)

    def test_log_write_failure_is_not_a_successful_zero_exit(self):
        self.m.ROOT = self.root
        with mock.patch.object(Path, "open", side_effect=OSError(28, "No space left on device")):
            with self.assertRaisesRegex(ValueError, "CAPTURE_LOG_INCOMPLETE"):
                self.m.capture([sys.executable, "-c", "print('must be recorded')"], dict(os.environ),
                               self.root / "out.log", self.root / "err.log", 5)

    def collection(self):
        inputs = self.root / "artifacts"
        inputs.mkdir()
        for shard in ("1/2", "2/2"):
            folder = inputs / ("pr396-capture-" + shard[0])
            shutil.copytree(self.folder, folder)
            receipt = copy.deepcopy(self.receipt)
            receipt["shard"] = shard
            receipt["environment"]["GEOMETRY_CDP_SHARD"] = shard
            receipt["scope"]["shard"]["index"] = int(shard[0])
            result = {**self.result, "scope": receipt["scope"]}
            raw = ("CDP_SCOPE " + json.dumps(receipt["scope"]) + "\nCDP_RESULT " + json.dumps(result) + "\n").encode()
            (folder / "stdout.log").write_bytes(raw)
            receipt["files"]["stdout.log"] = hashlib.sha256(raw).hexdigest()
            (folder / "manifest.json").write_text(json.dumps(receipt))
        self.m.ROOT = self.root / "checkout"
        self.m.ROOT.mkdir()
        return inputs

    def verify_collection(self, inputs, out, *, identities=None):
        fake_tool = SimpleNamespace(before_files=lambda _: {})
        with mock.patch.object(self.m, "source_identity", side_effect=identities or [self.expected] * 3), \
             mock.patch.object(self.m, "source_closure", return_value=self.closure), \
             mock.patch.object(self.m, "plan", return_value=self.plan), \
             mock.patch.object(self.m, "generator", return_value=(fake_tool, self.root / "T.patch", b"")), \
             mock.patch.object(self.m, "runtime_endpoint", return_value=18839), \
             mock.patch.object(self.m, "node", return_value={"passed": True, "acceptance": False, "P1161": 12}), \
             mock.patch.object(self.m, "candidates", return_value=({}, {})) as candidate:
            try:
                self.m.verify(inputs, out, self.root / "generator.py")
            finally:
                self.candidate_calls = candidate.call_count

    def assert_no_candidates_published(self, out):
        status = json.loads((out / "status.json").read_text())
        self.assertIs(status["acceptance"], False)
        self.assertIs(status["patches_written"], False)
        self.assertFalse((out / "manifest.json").exists())
        self.assertTrue(all(not (out / name).exists() for name in self.m.PATCH_NAMES))

    def test_missing_or_extra_partition_never_generates_candidates(self):
        inputs = self.collection()
        shutil.rmtree(inputs / "pr396-capture-2")
        out = self.root / "missing-output"
        with self.assertRaisesRegex(ValueError, "CAPTURE_TWO_RAW_SHARDS_REQUIRED"):
            self.verify_collection(inputs, out)
        self.assertEqual(self.candidate_calls, 0)
        self.assert_no_candidates_published(out)
        for name in ("pr396-capture-2", "extra-partition"):
            shutil.copytree(inputs / "pr396-capture-1", inputs / name)
        out = self.root / "extra-output"
        with self.assertRaisesRegex(ValueError, "CAPTURE_TWO_RAW_SHARDS_REQUIRED"):
            self.verify_collection(inputs, out)
        self.assertEqual(self.candidate_calls, 0)
        self.assert_no_candidates_published(out)

    def test_duplicate_partition_never_generates_candidates(self):
        inputs = self.collection()
        path = inputs / "pr396-capture-2/manifest.json"
        receipt = json.loads(path.read_text())
        receipt["shard"] = "1/2"
        path.write_text(json.dumps(receipt))
        out = self.root / "duplicate-output"
        with self.assertRaisesRegex(ValueError, "CAPTURE_DUPLICATE_SHARD"):
            self.verify_collection(inputs, out)
        self.assertEqual(self.candidate_calls, 0)
        self.assert_no_candidates_published(out)

    def test_source_change_before_judges_stops_generation(self):
        inputs = self.collection()
        changed = {**self.expected, "execution_sha": "0" * 40}
        out = self.root / "source-before-output"
        with self.assertRaisesRegex(ValueError, "CAPTURE_SOURCE_CHANGED"):
            self.verify_collection(inputs, out, identities=[self.expected, changed])
        self.assertEqual(self.candidate_calls, 0)
        self.assert_no_candidates_published(out)

    def test_source_change_during_judges_withholds_all_patches(self):
        inputs = self.collection()
        changed = {**self.expected, "execution_sha": "0" * 40}
        out = self.root / "source-after-output"
        with self.assertRaisesRegex(ValueError, "CAPTURE_SOURCE_CHANGED"):
            self.verify_collection(inputs, out, identities=[self.expected, self.expected, changed])
        self.assertEqual(self.candidate_calls, 1)
        self.assert_no_candidates_published(out)

    def test_generator_is_not_imported_until_T_is_also_verified(self):
        path = self.root / "PR396-complete-canvas.py"
        raw = b"# synthetic non-executable loader fixture\n"
        path.write_bytes(raw)
        path.with_name("PR396-canvas-T.patch").write_text("wrong patch\n")
        with mock.patch.object(self.m, "GENERATOR_BYTES", len(raw)), mock.patch.object(self.m, "GENERATOR_SHA", hashlib.sha256(raw).hexdigest()), mock.patch.object(self.m, "load_module") as imported:
            with self.assertRaisesRegex(ValueError, "CAPTURE_T_CHANGED"):
                self.m.generator(path)
            imported.assert_not_called()


def mutation_proof(out):
    out.mkdir(parents=True, exist_ok=False)
    original = SCRIPT.read_text()
    mutations = [
        ('R396_CAPTURE_IGNORE_RUN_ATTEMPT', 'for field in ("execution_sha", "head_sha", "tree", "run_id", "run_attempt"):', 'for field in ("execution_sha", "head_sha", "tree", "run_id"):', 1, 1),
        ('R396_CAPTURE_ACCEPT_BOOLEAN_EXIT', 'type(receipt.get("process_exit")) is int', 'isinstance(receipt.get("process_exit"), int)', 1, 1),
        ('R396_CAPTURE_IGNORE_RAW_HASH', 'and sha(path) == receipt["files"][name]', '', 1, 1),
        ('R396_CAPTURE_IGNORE_SOURCE_CLOSURE', 'require(json_read((folder / "source.json").read_bytes()) == closure, "CAPTURE_SOURCE_CHANGED")', 'require(True, "CAPTURE_SOURCE_CHANGED")', 1, 1),
        ('R396_CAPTURE_SKIP_FINAL_SOURCE_CHECK', 'require(source_identity() == expected and source_closure() == closure and plan() == original_plan,\n                "CAPTURE_SOURCE_CHANGED")', 'require(True, "CAPTURE_SOURCE_CHANGED")', 2, 2),
        ('R396_CAPTURE_ALLOW_INHERITED_ONLY', 'if key.startswith("GEOMETRY_") and (key.endswith(("_ONLY", "_CASES", "_CASE"))', 'if False and (key.endswith(("_ONLY", "_CASES", "_CASE"))', 1, 1),
        ('R396_CAPTURE_KEEP_FALSE_FULL_CLAIM', 'after[tool.TEST] = after[tool.TEST].replace(old, new, 1)', 'after[tool.TEST] = after[tool.TEST]', 1, 1),
        ('R396_CAPTURE_ACCEPT_URL_DRIFT', 'scope.get("url") == environment.get("GEOMETRY_TEST_URL")', 'True', 1, 1),
        ('R396_CAPTURE_ALLOW_2100_SECONDS', '0 <= elapsed < MAX_SECONDS', '0 <= elapsed <= MAX_SECONDS', 1, 1),
        ('R396_CAPTURE_SKIP_GENERATOR_HASH', 'require(len(raw) == GENERATOR_BYTES and hashlib.sha256(raw).hexdigest() == GENERATOR_SHA,', 'require(True,', 1, 1),
        ('R396_CAPTURE_SKIP_T_HASH', 'require(len(t_raw) == T_BYTES and hashlib.sha256(t_raw).hexdigest() == T_SHA, "CAPTURE_T_CHANGED")', 'require(True, "CAPTURE_T_CHANGED")', 1, 1),
        ('R396_CAPTURE_ALLOW_DIFFERENT_FLAGS', 'environment.get("GEOMETRY_CHROME_FLAGS") == "--no-sandbox"', 'True', 1, 1),
    ]

    def run(root, name, expected_exit):
        process = subprocess.run([sys.executable, '-B', str(root / Path(__file__).name)], capture_output=True, text=True, timeout=120)
        (out / (name + '.stdout')).write_text(process.stdout)
        (out / (name + '.stderr')).write_text(process.stderr)
        if process.returncode != expected_exit or not re.search(r'^Ran 31 tests in ', process.stderr, re.M):
            raise AssertionError('R396_CAPTURE_MUTATION_TEST_PROCESS:' + name)
        if expected_exit:
            found = re.search(r'^FAILED \(failures=(\d+)\)$', process.stderr, re.M)
            if found is None or int(found[1]) <= 0:
                raise AssertionError('R396_CAPTURE_MUTATION_NOT_NORMAL_FAILURE:' + name)
            failures = int(found[1])
        else:
            if not re.search(r'^OK$', process.stderr, re.M):
                raise AssertionError('R396_CAPTURE_MUTATION_BASELINE_FAILED:' + name)
            failures = 0
        return {'exitCode': process.returncode, 'tests': 31, 'failed': failures, 'errors': 0, 'skipped': 0}

    rows = []
    with tempfile.TemporaryDirectory(prefix='pr396-python-withdrawals-') as directory:
        root = Path(directory)
        shutil.copy2(Path(__file__), root / Path(__file__).name)
        script = root / SCRIPT.name
        for name, old, new, count, occurrence in mutations:
            if original.count(old) != count:
                raise AssertionError('R396_CAPTURE_MUTATION_ANCHOR:' + name)
            script.write_text(original)
            baseline = run(root, name + '-baseline', 0)
            at = -1
            for _ in range(occurrence):
                at = original.index(old, at + 1)
            script.write_text(original[:at] + new + original[at + len(old):])
            try:
                withdrawn = run(root, name + '-withdrawn', 1)
            finally:
                script.write_text(original)
            restored = run(root, name + '-restored', 0)
            rows.append({'name': name, 'baseline': baseline, 'withdrawn': withdrawn, 'restored': restored, 'result': 'killed'})
    result = {'kind': 'synthetic envelope unit tests; not browser acceptance', 'passed': True, 'mutations': rows}
    (out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == "__main__":
    if '--mutation-proof' in sys.argv:
        import argparse
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--mutation-proof', action='store_true')
        parser.add_argument('--output', type=Path, required=True)
        mutation_proof(parser.parse_args().output.resolve())
    else:
        unittest.main()
