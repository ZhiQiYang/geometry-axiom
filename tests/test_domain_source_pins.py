"""Real temporary source mutations through the three production pin consumers.

Native execution is deliberately outside this suite: mocked native receipts test
only pin plumbing and never stand in for a successful geometry verification.
"""
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "geometry-core", ROOT / "geometry-web"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import model_update as update
import scenario_verify as verifier
from geometry_app import source_closure
from modeling import ModelError, canonical_bytes
from rule_cases import runtime as rule_runtime
from rule_cases.catalog import case
from rule_cases.executor import refresh_receipt


DOMAINS = (
    "geometry-core/geometry_kernel/evaluator.py",
    "geometry-app/geometry_app/model_runtime.py",
    "geometry-templates/woodworking/geometry_woodworking/model_policy.py",
    "geometry-templates/woodworking/geometry_woodworking/catalog.json",
    "geometry-core/modeling/__init__.py",
    "geometry-app/geometry_app/provider.py",
    "geometry-templates/woodworking/geometry_woodworking/provider.py",
)
NATIVE = (
    "geometry-core/geometry_kernel/native/geometry.c",
    "geometry-app/native/app_model.h",
    "geometry-templates/woodworking/native/policy.inc",
    "current_geometry.c",
)
RULES = tuple("geometry-core/rule_cases/" + name
              for name in ("runtime.py", "definition.py", "catalog.py"))
WEB = tuple("geometry-web/" + name
            for name in ("model_update.py", "scenario_verify.py", "space_modeling.py", "web_bridge.c"))


def sha(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class DomainSourcePins(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="domain-source-pins-")))
        for name in (*DOMAINS, *NATIVE, *RULES, *WEB, "tests/binaries.py", "公理層.md", "root.h", "root.inc"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"version = 'a'\n")
        self.binary = self.root / "synthetic-not-executed.exe"
        self.binary.write_bytes(b"native bytes for a hash-only boundary control")
        self.binary.chmod(0o700)
        self.info = SimpleNamespace(state="fresh", reason="synthetic verified native boundary",
                                    fingerprint="c" * 64, path=self.binary)
        self.original_inventory = source_closure.source_inventory
        self.stack.enter_context(mock.patch.object(source_closure, "source_inventory",
            side_effect=lambda repository=None: self.original_inventory(self.root if repository is None else repository)))
        self.stack.enter_context(mock.patch.object(source_closure, "_LOADED", self.original_inventory(self.root)))
        for module, name in ((update, WEB[0]), (verifier, WEB[1]), (rule_runtime, RULES[0])):
            self.stack.enter_context(mock.patch.object(module, "ROOT", self.root))
            self.stack.enter_context(mock.patch.object(module, "__file__", str(self.root / name)))
        self.stack.enter_context(mock.patch.object(rule_runtime, "_REGISTRY_PATH", self.root / "tests/binaries.py"))
        self.stack.enter_context(mock.patch.object(rule_runtime, "_LOADED_MODULES", rule_runtime._module_hashes()))
        self.stack.enter_context(mock.patch.object(rule_runtime, "_LOADED_REGISTRY", sha(self.root / "tests/binaries.py")))
        self.inspect = self.stack.enter_context(mock.patch.object(rule_runtime.binaries, "inspect_one", return_value=self.info))

    def change_same_stat(self, name):
        path = self.root / name
        before = path.stat()
        original = path.read_bytes()
        changed = original.replace(b"'a'", b"'b'")
        self.assertNotEqual(original, changed)
        self.assertEqual(len(original), len(changed))
        path.write_bytes(changed)
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual((before.st_size, before.st_mtime_ns), (path.stat().st_size, path.stat().st_mtime_ns))
        return original

    def restore(self, name, original):
        (self.root / name).write_bytes(original)

    def reloaded_sources(self):
        """Explicitly model a new process; ordinary reads must never do this."""
        source_closure._LOADED = self.original_inventory(self.root)
        rule_runtime._LOADED_MODULES = rule_runtime._module_hashes()

    def identity(self):
        return rule_runtime.runtime_identity(self.binary)[0]

    def test_producer_tracks_each_moved_domain_with_same_size_and_mtime(self):
        before = update._producer_hash()
        for name in (*DOMAINS, *NATIVE):
            with self.subTest(source=name):
                original = self.change_same_stat(name)
                try:
                    self.assertNotEqual(before, update._producer_hash())
                finally:
                    self.restore(name, original)
        self.assertEqual(before, update._producer_hash())

    def test_producer_keeps_relative_path_lf_pair_digest(self):
        names = sorted((*DOMAINS, *NATIVE, WEB[0], WEB[2], WEB[3], "root.h", "root.inc"))
        expected = hashlib.sha256(canonical_bytes([[name, sha(self.root / name)] for name in names])).hexdigest()
        self.assertEqual(expected, update._producer_hash())
        before = update._producer_hash()
        for name in names:
            path = self.root / name
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(before, update._producer_hash())

    def test_producer_detects_new_and_removed_nested_code(self):
        before = update._producer_hash()
        path = self.root / "geometry-templates/woodworking/geometry_woodworking/nested/new_adapter.py"
        path.parent.mkdir()
        path.write_bytes(b"new adapter\n")
        added = update._producer_hash()
        self.assertNotEqual(before, added)
        path.unlink()
        self.assertEqual(before, update._producer_hash())
        (self.root / DOMAINS[0]).unlink()
        self.assertNotEqual(before, update._producer_hash())

    def test_model_runtime_hashes_actual_binary_bytes_and_rejects_loaded_source_change(self):
        before = update._runtime(self.binary, self.binary)
        self.assertEqual(hashlib.sha256(self.binary.read_bytes()).hexdigest(), before["base_binary_sha256"])
        self.assertEqual(before["base_binary_sha256"], before["bridge_binary_sha256"])
        self.assertEqual(sha(self.root / "公理層.md"), before["axiom_sha256"])
        loaded = source_closure._LOADED
        self.change_same_stat(DOMAINS[2])
        with self.assertRaises(ModelError) as caught:
            update._runtime(self.binary, self.binary)
        self.assertEqual("UPDATE_RUNTIME", caught.exception.code)
        self.assertEqual(loaded, source_closure._LOADED)

    def test_model_candidate_rejects_provider_change_without_mutating_record(self):
        result = {"source_sha256": "a" * 64, "summary": {}}
        record = {"id": "retained", "name": "Original", "created_at": "2026-10-16T00:00:00Z",
                  "source": {"kind": "scene", "placement_id": 1, "boundary_id": 1, "scene_hash": "a" * 64},
                  "input": {"mode": "plan", "base_scene": "", "placement_id": 1, "obstacles": [], "settings": {}},
                  "result": result}
        data = {"record": record, "current_scene": "", "selection": {"placement_id": 1, "boundary_id": 1,
                "edges": [0], "obstacles": [], "timbers": [], "projection": None}}
        before = canonical_bytes(data)
        base = {"base_scene": "", "placements": [{"id": 1, "boundary_id": 1}]}
        def changed(*args, **kwargs):
            self.change_same_stat(DOMAINS[2])
            return deepcopy(result)
        with mock.patch.object(update, "load_base", return_value=base), \
                mock.patch.object(update.space_modeling, "replay_stored", return_value=deepcopy(result)), \
                mock.patch.object(update.space_modeling, "preview", side_effect=changed), \
                mock.patch.object(update, "_graph", return_value={}), \
                mock.patch.object(update, "_protected", return_value=({}, {})), \
                self.assertRaises(ModelError) as caught:
            update.prepare_update(data, base_executable=self.binary, bridge_executable=self.binary)
        self.assertEqual("UPDATE_RUNTIME", caught.exception.code)
        self.assertEqual(before, canonical_bytes(data))

    def test_scenario_pins_track_each_moved_domain_and_keep_axiom_separate(self):
        for name in (*DOMAINS, *NATIVE):
            with self.subTest(source=name):
                before = verifier._validator_pins()
                original = self.change_same_stat(name)
                try:
                    with self.assertRaises(ModelError) as caught:
                        verifier._validator_pins()
                    self.assertEqual("SCENARIO_RUNTIME", caught.exception.code)
                    self.reloaded_sources()
                    after = verifier._validator_pins()
                    self.assertNotEqual(before["validator_sha256"], after["validator_sha256"])
                    self.assertEqual(before["axiom_sha256"], after["axiom_sha256"])
                finally:
                    self.restore(name, original)
                    self.reloaded_sources()

    def test_scenario_keeps_relative_path_lf_pair_digest(self):
        names = sorted((*DOMAINS, *NATIVE, WEB[1], WEB[2], "tests/binaries.py"))
        expected = hashlib.sha256(canonical_bytes([[name, sha(self.root / name)] for name in names])).hexdigest()
        self.assertEqual(expected, verifier._validator_pins()["validator_sha256"])
        for name in names:
            path = self.root / name
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(expected, verifier._validator_pins()["validator_sha256"])

    def test_scenario_addition_and_deletion_reject_old_loaded_identity(self):
        before = verifier._validator_pins()
        loaded = source_closure._LOADED
        path = self.root / "geometry-core/geometry_kernel/new_evaluator.py"
        path.write_bytes(b"added\n")
        with self.assertRaises(ModelError) as caught:
            verifier._validator_pins()
        self.assertEqual("SCENARIO_RUNTIME", caught.exception.code)
        self.assertEqual(loaded, source_closure._LOADED)
        path.unlink()
        self.assertEqual(before, verifier._validator_pins())
        (self.root / DOMAINS[3]).unlink()
        with self.assertRaises(ModelError) as caught:
            verifier._validator_pins()
        self.assertEqual("SCENARIO_RUNTIME", caught.exception.code)
        self.assertEqual(loaded, source_closure._LOADED)
    def test_scenario_verification_rejects_kernel_change_without_mutating_input(self):
        data = {"manifest": {"models": []}, "scene": ""}
        before = canonical_bytes(data)
        native = {"ok": True, "capabilities": [], "required_capabilities": [],
                  "final_objects": {"boundaries": [], "placements": []}, "final_scene": ""}
        def changed(*args, **kwargs):
            self.change_same_stat(DOMAINS[0])
            return (json.dumps(native) + "\n{}\n").encode()
        with mock.patch.object(verifier, "_run_bounded", side_effect=changed), \
                mock.patch.object(verifier, "_inventory", return_value=([], [])), \
                self.assertRaises(ModelError) as caught:
            verifier.verify_project(data, bridge_executable=self.binary)
        self.assertEqual("SCENARIO_RUNTIME", caught.exception.code)
        self.assertEqual(before, canonical_bytes(data))

    def test_scenario_source_receipt_remains_the_verified_native_fingerprint(self):
        for base, name in ((False, "bridge"), (True, "model-base")):
            with self.subTest(binary=name):
                self.assertEqual("c" * 64, verifier._source_receipt(self.binary, base=base))
                self.inspect.assert_called_with(verifier.binaries.BY_NAME[name], path=self.binary)
                bad = SimpleNamespace(state="stale", fingerprint="c" * 64, path=self.binary)
                with mock.patch.object(verifier.binaries, "inspect_one", return_value=bad), self.assertRaises(ModelError) as caught:
                    verifier._source_receipt(self.binary, base=base)
                self.assertEqual("SCENARIO_RUNTIME_UNKNOWN", caught.exception.code)

    def test_rule_identity_keeps_full_relative_paths_and_original_aggregation(self):
        value = self.identity()
        self.assertTrue(value["known"], value)
        expected = hashlib.sha256()
        for name in sorted((*DOMAINS, *NATIVE, *RULES)):
            expected.update(name.encode() + b"\0" + bytes.fromhex(sha(self.root / name)))
        expected.update(b"tests/binaries.py\0" + bytes.fromhex(sha(self.root / "tests/binaries.py")))
        self.assertEqual(expected.hexdigest(), value["validatorVersion"])
        self.assertEqual({"known", "nativeBinaryHash", "nativeSourceHash", "validatorVersion", "axiomHash", "assertionSchemaHash"}, set(value))
        self.assertEqual("c" * 64, value["nativeSourceHash"])
        self.assertEqual(sha(self.root / RULES[1]), value["assertionSchemaHash"])

    def test_rule_loaded_snapshot_cannot_be_relabelled_after_moved_source_changes(self):
        for name in (*DOMAINS, *NATIVE, RULES[2]):
            with self.subTest(source=name):
                before = self.identity()
                loaded = deepcopy(rule_runtime._LOADED_MODULES)
                original = self.change_same_stat(name)
                try:
                    changed = self.identity()
                    self.assertFalse(changed["known"], changed)
                    self.assertIn("reload", changed["reason"])
                    self.assertEqual(loaded, rule_runtime._LOADED_MODULES)
                    self.reloaded_sources()
                    reloaded = self.identity()
                    self.assertTrue(reloaded["known"], reloaded)
                    self.assertNotEqual(before["validatorVersion"], reloaded["validatorVersion"])
                finally:
                    self.restore(name, original)
                    self.reloaded_sources()

    def test_rule_addition_and_deletion_do_not_update_loaded_snapshot(self):
        loaded = deepcopy(rule_runtime._LOADED_MODULES)
        path = self.root / "geometry-app/geometry_app/new_adapter.py"
        path.write_bytes(b"added\n")
        self.assertFalse(self.identity()["known"])
        self.assertEqual(loaded, rule_runtime._LOADED_MODULES)
        path.unlink()
        self.assertTrue(self.identity()["known"])
        (self.root / DOMAINS[2]).unlink()
        self.assertFalse(self.identity()["known"])
        self.assertEqual(loaded, rule_runtime._LOADED_MODULES)

    def test_rule_second_read_rejects_source_replacement_during_verification(self):
        calls = 0
        def changed(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                self.change_same_stat(DOMAINS[1])
            return self.info
        self.inspect.side_effect = changed
        value = self.identity()
        self.assertEqual(2, calls)
        self.assertFalse(value["known"])
        self.assertEqual("Runtime changed during verification", value["reason"])

    def test_rule_registry_still_participates_in_loaded_identity(self):
        before = self.identity()
        self.assertTrue(before["known"], before)
        self.change_same_stat("tests/binaries.py")
        self.assertFalse(self.identity()["known"])

    def test_retained_rule_receipt_becomes_stale_without_changing_evidence(self):
        receipt = json.loads((ROOT / "tests/fixtures/rule_case_generic_immutable_receipt.json").read_text(encoding="utf-8"))
        receipt["executor"] = self.identity()
        retained = deepcopy(receipt)
        self.change_same_stat(DOMAINS[3])
        refreshed = refresh_receipt(receipt, case("fixed-version-immutable"), self.identity())
        self.assertEqual("stale", refreshed["status"])
        self.assertIn("unknown-runtime", refreshed["staleReasons"])
        self.assertEqual(retained, receipt)
        self.assertEqual(retained["observations"], refreshed["observations"])


if __name__ == "__main__":
    unittest.main()
