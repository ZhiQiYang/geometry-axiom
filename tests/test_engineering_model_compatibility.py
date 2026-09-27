"""Engineering capability boundaries and exact known-axiom compatibility."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
import modeling
from modeling import ModelError, build_package, verify_package
from modeling.base import load_base
from modeling.common import canonical_bytes, digest, scene_required_capabilities

LEGACY_VERSION = ("494660068ceb884c1a96884a2b704e3bcf5d24ca", "bc01cf0db266f97255156e28e40fb235833031fb95f1f234ad6d90a9f08240f8")
CASE = json.loads((ROOT / "geometry-core/modeling-cases.json").read_text())["cases"][0]


class EngineeringAdapterProtocol(unittest.TestCase):
    def snapshot(self, scene="", capabilities=None):
        value = {"ok": True, "schema": "geometry-base-snapshot/1", "base_scene": scene,
                 "specs": [], "placements": [], "solids": [], "unplaced_timbers": [], "dependencies": []}
        if capabilities is not None:
            value["required_capabilities"] = capabilities
        return value

    def adapter(self, source, snapshot):
        output = SimpleNamespace(stdout=canonical_bytes(snapshot), returncode=0)
        with mock.patch("modeling.base.subprocess.run", return_value=output):
            return load_base(source, executable="test-only-adapter")

    def test_old_snapshot_protocol_is_accepted_for_legacy_sources_only(self):
        self.adapter("", self.snapshot())
        with self.assertRaises(ModelError) as caught:
            self.adapter("requires engineering-spec/1\n", self.snapshot())
        self.assertEqual(caught.exception.code, "BASE_PROTOCOL")

    def test_adapter_must_preserve_source_marker_and_required_capabilities(self):
        source = "requires engineering-spec/1\nengineering material encoded-source\n"
        self.adapter(source, self.snapshot(source, ["engineering-spec/1"]))
        for snapshot in [self.snapshot(source), self.snapshot("", ["engineering-spec/1"]),
                         self.snapshot(source, ["engineering-spec/2"]),
                         self.snapshot(source, ["engineering-spec/1", "engineering-spec/1"])]:
            with self.subTest(snapshot=snapshot), self.assertRaises(ModelError):
                self.adapter(source, snapshot)

    def test_unknown_required_schema_and_stripped_markers_never_hide_sources(self):
        with self.assertRaises(ModelError) as caught:
            load_base("requires engineering-spec/9\n", executable="never-executed")
        self.assertEqual(caught.exception.code, "CAPABILITY")
        self.assertEqual(scene_required_capabilities("# requires engineering-spec/9\n"), set())
        self.assertEqual(scene_required_capabilities("engineering grid payload\n"), {"engineering-spec/1"})


class EngineeringModelCompatibility(unittest.TestCase):
    def build(self):
        return build_package(deepcopy(CASE["definitions"]), deepcopy(CASE["request"]))

    def test_legacy_definitions_do_not_gain_engineering_capability(self):
        package = self.build()
        self.assertNotIn("engineering-spec/1", package["manifest"]["capabilities"])
        self.assertEqual(verify_package(package)["derived"], package["derived"])

    def test_exact_known_legacy_revision_rebuilds_without_mutating_saved_package(self):
        package = self.build()
        package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = LEGACY_VERSION
        original = deepcopy(package)
        rebuilt = verify_package(package)
        self.assertEqual(package, original)
        for key in ("definitions", "request", "derived"):
            self.assertEqual(rebuilt[key], package[key])
        self.assertIn(LEGACY_VERSION, modeling.LEGACY_AXIOM_VERSIONS)

    def test_unknown_revision_or_mixed_revision_hash_pair_is_rejected(self):
        for version in [("0" * 40, LEGACY_VERSION[1]), (LEGACY_VERSION[0], "0" * 64),
                        ("0" * 40, "0" * 64), (LEGACY_VERSION[0], modeling.AXIOM_SHA256),
                        (modeling.AXIOM_REVISION, LEGACY_VERSION[1])]:
            package = self.build()
            package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = version
            with self.subTest(version=version), self.assertRaises(ModelError) as caught:
                verify_package(package)
            self.assertEqual(caught.exception.code, "AXIOM_VERSION")

    def test_rehashed_legacy_snapshot_corruption_still_rebuilds_and_rejects(self):
        package = self.build()
        package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = LEGACY_VERSION
        package["derived"]["objects"][0]["vertices_mm"][0][0] += 1
        package["manifest"]["geometry_sha256"] = digest(package["derived"])
        with self.assertRaises(ModelError) as caught:
            verify_package(package)
        self.assertEqual(caught.exception.code, "SNAPSHOT_MISMATCH")

    def test_engineering_sources_cannot_claim_the_known_legacy_axioms(self):
        package = self.build()
        package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = LEGACY_VERSION
        # Simulate a future additive current version while keeping this test valid
        # during the synchronized SSOT transition. The old source cannot opt in.
        with mock.patch.object(modeling, "AXIOM_REVISION", "1" * 40), mock.patch.object(modeling, "_axiom_hash", return_value="2" * 64):
            for change in ("source", "capability"):
                bad = deepcopy(package)
                if change == "source":
                    bad["definitions"]["base_scene"] = "requires engineering-spec/1\n" + bad["definitions"]["base_scene"]
                    bad["manifest"]["source_sha256"] = digest(bad["definitions"])
                else:
                    bad["manifest"]["capabilities"].append("engineering-spec/1")
                with self.subTest(change=change), self.assertRaises(ModelError) as caught:
                    verify_package(bad)
                self.assertEqual(caught.exception.code, "AXIOM_VERSION")

    def test_base_required_capability_reaches_manifest_and_cannot_be_removed(self):
        base = load_base(CASE["definitions"]["base_scene"])
        base["base_scene"] = "requires engineering-spec/1\n" + base["base_scene"]
        base["required_capabilities"] = ["engineering-spec/1"]
        definitions = deepcopy(CASE["definitions"])
        definitions["base_scene"] = base["base_scene"]
        # Only adapter transport is substituted here; actual engineering source
        # evaluation is covered by native core fixtures, not this boundary test.
        with mock.patch("modeling.base.load_base", return_value=base):
            package = build_package(definitions, CASE["request"])
            self.assertIn("engineering-spec/1", package["manifest"]["capabilities"])
            self.assertEqual(package["definitions"]["base_scene"], base["base_scene"])
            with self.assertRaises(ModelError) as caught:
                build_package(definitions, CASE["request"], capabilities=[c for c in modeling.CAPABILITIES if c != "engineering-spec/1"])
            self.assertEqual(caught.exception.code, "CAPABILITY")


if __name__ == "__main__":
    unittest.main()
