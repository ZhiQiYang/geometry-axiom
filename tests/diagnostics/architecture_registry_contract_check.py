"""R386 architecture fragment gate; run explicitly, never invent a suite cost.

The ordinary architecture unit/product suites still exercise the unchanged
Scanner. This additional gate proves storage migration and named withdrawals.
"""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

_arguments = argparse.ArgumentParser(add_help=False)
_arguments.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
_options, _remaining = _arguments.parse_known_args()
sys.path.insert(0, str(_options.root.resolve() / "tests"))
import architecture_contract as architecture


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def fixture(root):
    (root / "src").mkdir()
    (root / "src/core.py").write_bytes(b"value = 1\n")
    (root / "src/other.py").write_bytes(b"value = 2\n")
    excluded = b"value = 3\n"
    (root / "src/driver.py").write_bytes(excluded)
    sources = [{"path": "src/" + name + ".py", "layer": "K", "language": "python",
                "purpose": "R386 synthetic core source"} for name in ("core", "other")]
    return {
        "schema": "geometry-architecture/1", "sourceRoots": ["src"], "sourceFiles": [],
        "searchRoots": {"c": ["src"], "python": ["src"], "javascript": ["src"]},
        "sources": sources,
        "exclusions": [{"path": "src/driver.py", "reason": "Synthetic test driver",
                        "sha256": hashlib.sha256(excluded).hexdigest(), "hashMode": "lf"}],
        "htmlScriptRoutes": [], "javascriptImportRoutes": [], "htmlEmbedRoutes": [],
        "trustedVendorBundles": [],
        "policy": {"cSystemHeaders": [], "pythonStdlib": [], "javascriptBuiltins": [],
                   "externalModules": [], "forbiddenIdentifiers": [], "forbiddenStrings": [],
                   "forbiddenModules": {"c": [], "python": [], "javascript": []}},
    }


def write_fragments(root, manifest):
    """Independent fixture writer makes T red on the pre-fragment loader."""
    collections = ("sources", "exclusions", "htmlScriptRoutes", "javascriptImportRoutes",
                   "htmlEmbedRoutes", "trustedVendorBundles")
    config = {key: deepcopy(value) for key, value in manifest.items() if key not in collections}
    path = root / "product-architecture.json"
    path.write_bytes(encoded({"schema": "geometry-architecture-fragments/1",
                              "fragments": "product-architecture.d", "config": config}))
    for collection in ("sources", "exclusions"):
        for entry in manifest[collection]:
            target = root / "product-architecture.d" / collection / (entry["path"] + ".json")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(encoded({"schema": "geometry-architecture-entry/1",
                                        "collection": collection, "entry": entry}))
    return path


class ArchitectureRegistryContract(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="geo386-architecture-registry-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manifest = fixture(self.root)
        self.path = write_fragments(self.root, self.manifest)
        self.directory = self.root / "product-architecture.d"
        self.core = self.directory / "sources/src/core.py.json"
        self.excluded = self.directory / "exclusions/src/driver.py.json"

    def result(self):
        return architecture.scan(self.root, architecture.load_manifest(self.path))

    def rejects_load(self, code):
        with self.assertRaises(architecture.ContractError) as caught:
            architecture.load_manifest(self.path)
        self.assertEqual(caught.exception.diagnostic.code, code)

    def test_fragmented_manifest_preserves_the_complete_scanner_result(self):
        expected = architecture.scan(self.root, self.manifest)
        self.assertTrue(expected.ok, expected.to_dict())
        actual = self.result()
        self.assertEqual(actual.to_dict(), expected.to_dict())

    def test_legacy_manifest_is_still_read_without_projection(self):
        self.path.write_bytes(encoded(self.manifest))
        self.assertEqual(architecture.load_manifest(self.path), self.manifest)

    def test_missing_fragment_keeps_complete_inventory_gate(self):
        self.core.unlink()
        self.assertIn("SOURCE_UNREGISTERED", [row.code for row in self.result().diagnostics])

    def test_exclusion_digest_is_still_exact(self):
        (self.root / "src/driver.py").write_bytes(b"value = 4\n")
        self.assertIn("EXCLUSION_DIGEST", [row.code for row in self.result().diagnostics])

    def test_duplicate_source_exclusion_is_rejected(self):
        entry = {"path": "src/core.py", "reason": "Cannot hide an owned source",
                 "sha256": hashlib.sha256((self.root / "src/core.py").read_bytes()).hexdigest()}
        target = self.directory / "exclusions/src/core.py.json"
        target.write_bytes(encoded({"schema": "geometry-architecture-entry/1",
                                   "collection": "exclusions", "entry": entry}))
        self.rejects_load("FRAGMENT_IDENTITY")

    def test_duplicate_json_key_is_rejected(self):
        self.core.write_bytes(self.core.read_bytes().replace(b'"entry": {', b'"entry": {}, "entry": {'))
        self.rejects_load("MANIFEST_DUPLICATE_KEY")

    def test_unknown_fragment_keys_are_rejected(self):
        row = json.loads(self.core.read_bytes())
        row["ignored"] = True
        self.core.write_bytes(encoded(row))
        self.rejects_load("MANIFEST_SCHEMA")

    def test_wrong_fragment_schema_is_rejected(self):
        row = json.loads(self.core.read_bytes())
        row["schema"] = "geometry-architecture-entry/99"
        self.core.write_bytes(encoded(row))
        self.rejects_load("FRAGMENT_SCHEMA")

    def test_unknown_collection_is_rejected(self):
        row = json.loads(self.core.read_bytes())
        row["collection"] = "optionalSources"
        self.core.write_bytes(encoded(row))
        self.rejects_load("FRAGMENT_COLLECTION")

    def test_filename_and_identity_must_match(self):
        self.core.rename(self.core.with_name("alias.py.json"))
        self.rejects_load("FRAGMENT_NAME")

    def test_fragment_file_symlink_is_rejected(self):
        saved = self.root / "saved.json"
        self.core.rename(saved)
        self.core.symlink_to(saved)
        self.rejects_load("FRAGMENT_SYMLINK")

    def test_fragment_directory_symlink_is_rejected(self):
        moved = self.root / "moved"
        self.directory.rename(moved)
        self.directory.symlink_to(moved, target_is_directory=True)
        self.rejects_load("FRAGMENT_SYMLINK")

    def test_manifest_file_symlink_is_rejected(self):
        saved = self.root / "saved.json"
        self.path.rename(saved)
        self.path.symlink_to(saved)
        self.rejects_load("FRAGMENT_SYMLINK")

    def test_parent_alias_is_rejected(self):
        row = json.loads(self.path.read_bytes())
        row["fragments"] = "../product-architecture.d"
        self.path.write_bytes(encoded(row))
        self.rejects_load("FRAGMENT_DIRECTORY")

    def test_non_json_file_cannot_disappear_from_closure(self):
        (self.directory / "note.txt").write_bytes(b"unreviewed input\n")
        self.rejects_load("FRAGMENT_FILE")

    def test_casefold_identity_collision_is_rejected(self):
        row = json.loads(self.core.read_bytes())
        row["entry"]["path"] = "src/Core.py"
        (self.core.parent / "Core.py.json").write_bytes(encoded(row))
        self.rejects_load("FRAGMENT_IDENTITY")

    def test_missing_fragment_directory_is_rejected(self):
        self.directory.rename(self.root / "removed")
        self.rejects_load("FRAGMENT_DIRECTORY")

    def test_root_cannot_smuggle_another_sources_array(self):
        row = json.loads(self.path.read_bytes())
        row["config"]["sources"] = []
        self.path.write_bytes(encoded(row))
        self.rejects_load("MANIFEST_SCHEMA")

    def test_closure_binds_fragment_metadata_without_product_changes(self):
        before = architecture.manifest_input_bytes(self.path)
        row = json.loads(self.core.read_bytes())
        row["entry"]["purpose"] += " reviewed metadata edit"
        self.core.write_bytes(encoded(row))
        self.assertNotEqual(architecture.manifest_input_bytes(self.path), before)

    def test_closure_binds_fragment_exact_lf_bytes(self):
        before = architecture.manifest_input_bytes(self.path)
        self.core.write_bytes(self.core.read_bytes() + b"\n")
        self.assertNotEqual(architecture.manifest_input_bytes(self.path), before)

    def test_closure_keeps_the_existing_explicit_lf_normalization(self):
        before = architecture.manifest_input_bytes(self.path)
        for path in architecture.manifest_input_paths(self.path):
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(architecture.manifest_input_bytes(self.path), before)

    def test_legacy_input_bytes_keep_old_receipt_semantics(self):
        raw = encoded(self.manifest)
        self.path.write_bytes(raw.replace(b"\n", b"\r\n"))
        self.assertEqual(architecture.manifest_input_bytes(self.path), raw)

    def test_migration_is_deterministic_and_does_not_mutate_input(self):
        original = deepcopy(self.manifest)
        output = architecture.fragment_manifest_files(self.manifest)
        reversed_input = deepcopy(self.manifest)
        reversed_input["sources"].reverse()
        self.assertEqual(output, architecture.fragment_manifest_files(reversed_input))
        self.assertEqual(self.manifest, original)
        self.assertTrue(all(b"\r" not in raw and raw.endswith(b"\n") for raw in output.values()))
        for name, raw in output.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        self.assertTrue(self.result().ok, self.result().to_dict())
        self.assertEqual(architecture.fragment_manifest_files(architecture.load_manifest(self.path)), output)

    def test_two_additions_change_disjoint_files_and_union_without_edits(self):
        base = architecture.fragment_manifest_files(self.manifest)
        additions = []
        for name in ("alpha", "omega"):
            candidate = deepcopy(self.manifest)
            candidate["sources"].append({"path": "src/" + name + ".py", "layer": "K",
                                         "language": "python", "purpose": "Independent new source"})
            result = architecture.fragment_manifest_files(candidate)
            self.assertTrue(all(result[key] == raw for key, raw in base.items()))
            additions.append(set(result) - set(base))
            for key in additions[-1]:
                target = self.root / key
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(result[key])
            (self.root / "src" / (name + ".py")).write_bytes(b"value = 5\n")
        self.assertEqual([len(item) for item in additions], [1, 1])
        self.assertFalse(additions[0] & additions[1])
        self.assertEqual(len(self.result().sources), 4)
        self.assertTrue(self.result().ok, self.result().to_dict())

    def test_route_identity_collision_is_rejected_before_writing(self):
        row = {"source": "src/page.html", "src": "app.js", "target": "src/app.js", "purpose": "Fixture route"}
        self.manifest["htmlScriptRoutes"] = [row, dict(row, purpose="Other route with same identity")]
        with self.assertRaises(architecture.ContractError) as caught:
            architecture.fragment_manifest_files(self.manifest)
        self.assertEqual(caught.exception.diagnostic.code, "FRAGMENT_IDENTITY")

    def test_every_route_and_trust_collection_round_trips(self):
        self.manifest["htmlScriptRoutes"] = [{"source": "src/a.html", "src": "app.js", "target": "src/a.js", "purpose": "Exact script"}]
        self.manifest["javascriptImportRoutes"] = [{"source": "src/a.js", "specifier": "asset.js", "target": "src/b.js", "purpose": "Exact import"}]
        self.manifest["htmlEmbedRoutes"] = [{"source": "src/a.html", "elementId": "frame", "driver": "src/a.js"}]
        self.manifest["trustedVendorBundles"] = [{"id": "test-bundle", "files": ["src/b.js"], "layers": ["H"], "purpose": "Exact trust"}]
        output = architecture.fragment_manifest_files(self.manifest)
        for name, raw in output.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        result = architecture.load_manifest(self.path)
        for key in ("htmlScriptRoutes", "javascriptImportRoutes", "htmlEmbedRoutes", "trustedVendorBundles"):
            self.assertEqual(result[key], self.manifest[key])

    def review_fixture(self, new=False):
        relative = "geometry-web/canvas_registry.js" if new else "geometry-web/canvas_shards.js"
        source = self.root / relative
        source.parent.mkdir(exist_ok=True)
        source.write_bytes(b"'use strict';\n")
        before = deepcopy(self.manifest)
        if not new:
            before["exclusions"].append({"path": relative, "reason": "Existing exact test driver",
                                         "hashMode": "lf", "sha256": "a" * 64})
        reviews = architecture.source_review_files(before, self.root, [relative])
        for name, raw in reviews.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        return before, relative, source, reviews

    def test_reviewed_source_addition_requires_the_exact_new_helper(self):
        before, relative, source, reviews = self.review_fixture(new=True)
        result, report = architecture.apply_reviewed_source_updates(before, self.root)
        self.assertEqual(len(result["exclusions"]), len(before["exclusions"]) + 1)
        self.assertEqual(report[0]["action"], "add")
        self.assertEqual(report[0]["afterSha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertNotIn(relative, {entry["path"] for entry in before["exclusions"]})

    def test_reviewed_source_updates_only_its_original_exclusion(self):
        before, relative, source, reviews = self.review_fixture()
        result, report = architecture.apply_reviewed_source_updates(before, self.root)
        self.assertEqual(report[0]["action"], "update")
        self.assertEqual(result["sources"], before["sources"])
        self.assertEqual(result["exclusions"][:-1], before["exclusions"][:-1])
        self.assertEqual(result["exclusions"][-1]["reason"], before["exclusions"][-1]["reason"])
        self.assertEqual(before["exclusions"][-1]["sha256"], "a" * 64)

    def test_reviewed_source_rejects_any_unreviewed_after_bytes(self):
        before, relative, source, reviews = self.review_fixture()
        source.write_bytes(source.read_bytes() + b"// new code requires review\n")
        with self.assertRaises(architecture.ContractError) as caught:
            architecture.apply_reviewed_source_updates(before, self.root)
        self.assertEqual(caught.exception.diagnostic.code, "SOURCE_REVIEW_AFTER")

    def test_reviewed_source_rejects_a_different_before_pin(self):
        before, relative, source, reviews = self.review_fixture()
        before["exclusions"][-1]["sha256"] = "b" * 64
        with self.assertRaises(architecture.ContractError) as caught:
            architecture.apply_reviewed_source_updates(before, self.root)
        self.assertEqual(caught.exception.diagnostic.code, "SOURCE_REVIEW_BEFORE")

    def test_review_does_not_overwrite_a_fresh_pin_from_a_later_main(self):
        before, relative, source, reviews = self.review_fixture()
        source.write_bytes(source.read_bytes() + b"// already reviewed by later main\n")
        before["exclusions"][-1]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        result, report = architecture.apply_reviewed_source_updates(before, self.root)
        self.assertEqual(result, before)
        self.assertEqual(report[0]["action"], "already-current")

    def test_review_generator_rejects_an_unrelated_source(self):
        with self.assertRaises(architecture.ContractError) as caught:
            architecture.source_review_files(self.manifest, self.root, ["src/core.py"])
        self.assertEqual(caught.exception.diagnostic.code, "SOURCE_REVIEW_SCOPE")

    def test_review_generator_cannot_reclassify_an_owned_source(self):
        before, relative, source, reviews = self.review_fixture(new=True)
        before["sources"].append({"path": relative, "layer": "H", "language": "javascript", "purpose": "Owned source"})
        with self.assertRaises(architecture.ContractError) as caught:
            architecture.source_review_files(before, self.root, [relative])
        self.assertEqual(caught.exception.diagnostic.code, "SOURCE_REVIEW_SCOPE")

    def test_review_generation_is_deterministic_pure_lf(self):
        before, relative, source, reviews = self.review_fixture()
        self.assertEqual(reviews, architecture.source_review_files(before, self.root, [relative]))
        self.assertTrue(all(b"\r" not in raw and raw.endswith(b"\n") for raw in reviews.values()))

    def test_review_input_symlink_is_rejected(self):
        before, relative, source, reviews = self.review_fixture()
        receipt = self.root / next(iter(reviews))
        saved = self.root / "saved-review.json"
        receipt.rename(saved)
        receipt.symlink_to(saved)
        with self.assertRaises(architecture.ContractError) as caught:
            architecture.apply_reviewed_source_updates(before, self.root)
        self.assertEqual(caught.exception.diagnostic.code, "SOURCE_REVIEW_SYMLINK")


def load_tests(loader, tests, pattern):
    """The tests-only patch fails once, explicitly, on the unfragmented base.

    Once all public entry points exist, unittest runs every contract test.
    A partial/stub implementation therefore gets no bypass for a failed case.
    """
    required = ("fragment_manifest_files", "manifest_input_bytes", "manifest_input_paths",
                "source_review_files", "apply_reviewed_source_updates")
    missing = [name for name in required if not callable(getattr(architecture, name, None))]
    if not missing:
        return tests

    def missing_registry_contract():
        raise AssertionError("R386 architecture registry contract is absent: " + ", ".join(missing))

    return unittest.TestSuite([unittest.FunctionTestCase(missing_registry_contract)])


def withdrawals():
    """Execute real reader/scanner before, during and after each exact withdrawal."""
    records = []
    with tempfile.TemporaryDirectory(prefix="geo386-architecture-withdrawals-") as folder:
        root = Path(folder)
        original = fixture(root)
        path = write_fragments(root, original)
        fragment = root / "product-architecture.d/sources/src/core.py.json"
        excluded = root / "src/driver.py"

        def check():
            try:
                result = architecture.scan(root, architecture.load_manifest(path))
                return 0 if result.ok else 1
            except (architecture.ContractError, OSError, ValueError):
                return 1

        for name, target, replacement in (
                ("R386_ARCH_FRAGMENT_MISSING", fragment, None),
                ("R386_ARCH_EXCLUSION_BYTES_MISMATCH", excluded, b"value = 99\n"),
                ("R386_ARCH_FRAGMENT_WRONG_IDENTITY", fragment,
                 fragment.read_bytes().replace(b"src/core.py", b"src/missing.py"))):
            before = check()
            saved = target.read_bytes()
            try:
                if replacement is None:
                    target.unlink()
                else:
                    target.write_bytes(replacement)
                during = check()
            finally:
                target.write_bytes(saved)
            after = check()
            record = {"name": name, "exitCodes": [before, during, after]}
            if record["exitCodes"] != [0, 1, 0]:
                raise AssertionError(record)
            records.append(record)
        helper = root / "geometry-web/canvas_registry.js"
        helper.parent.mkdir()
        helper.write_bytes(b"'use strict';\n")
        original["sourceRoots"].append("geometry-web")
        for name, raw in architecture.source_review_files(
                original, root, ["geometry-web/canvas_registry.js"]).items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)

        def reviewed():
            try:
                expanded, _ = architecture.apply_reviewed_source_updates(original, root)
                return 0 if architecture.scan(root, expanded).ok else 1
            except (architecture.ContractError, OSError, ValueError):
                return 1

        before, saved = reviewed(), helper.read_bytes()
        try:
            helper.write_bytes(saved + b"// unreviewed code\n")
            during = reviewed()
        finally:
            helper.write_bytes(saved)
        record = {"name": "R386_ARCH_UNREVIEWED_PIN_REFRESH", "exitCodes": [before, during, reviewed()]}
        if record["exitCodes"] != [0, 1, 0]:
            raise AssertionError(record)
        records.append(record)
    return records


if __name__ == "__main__":
    if _remaining == ["--withdrawals"]:
        print(json.dumps(withdrawals(), ensure_ascii=False, indent=2))
    else:
        unittest.main(argv=[sys.argv[0], *_remaining])
