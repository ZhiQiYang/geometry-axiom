"""GEO-261: replay immutable pre-adoption packages with exact version gates.

Accepted fixtures are untouched output of released main a898ad6e. Deliberate
manifest/source alterations below are negative probes, never old-producer
evidence. Source subdivision remains unsupported by this model executor.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
import modeling
from modeling import ModelError, build_package, verify_package
from modeling.common import digest

FIXTURES = ROOT / "tests/fixtures/domain-decoupling-main-a898ad6e"
PRODUCER = "a898ad6e12707104568679591fe1b21804bfc3df"
PRE_DECOUPLING = ("b3c79615d0cde89bbdca72c1223d214324bc5f8f",
                  "e5e43ec5da2030669c9ecd7a67f8b250cfb7290cf663365b2b66c51814bb77b9")
RECEIPT_SHA256 = "4660414637141df3cfa8da3c392bb17ae33b7c96ff1c35eb8b86827d0eb707e1"


def fixture(name):
    return json.loads((FIXTURES / (name + ".json")).read_bytes())


class DomainDecouplingCompatibility(unittest.TestCase):
    def assert_rebuild_only_updates_axiom_version(self, name):
        path = FIXTURES / (name + ".json")
        raw = path.read_bytes()
        package = json.loads(raw)
        original = deepcopy(package)
        manifest = original["manifest"]
        self.assertEqual((manifest["axiom_revision"], manifest["axiom_sha256"]), PRE_DECOUPLING)
        self.assertNotEqual((modeling.AXIOM_REVISION, modeling.AXIOM_SHA256), PRE_DECOUPLING,
                            "This suite must exercise the actual post-adoption version")
        rebuilt = verify_package(package)
        self.assertEqual(package, original, "verification must not upgrade saved provenance in place")
        self.assertEqual(path.read_bytes(), raw, "the genuine old-producer bytes must remain intact")
        expected = deepcopy(original)
        expected["manifest"]["axiom_revision"] = modeling.AXIOM_REVISION
        expected["manifest"]["axiom_sha256"] = modeling.AXIOM_SHA256
        self.assertEqual(rebuilt, expected,
                         "definitions/request/derived/diagnostics and every other manifest field must stay exact")
        return rebuilt

    def assert_version_rejection(self, package):
        original = deepcopy(package)
        with self.assertRaises(ModelError) as caught:
            verify_package(package)
        self.assertEqual((caught.exception.status, caught.exception.code, caught.exception.clause),
                         ("UNSUPPORTED", "AXIOM_VERSION", "I32"))
        self.assertEqual(package, original, "refusal must preserve the supplied package")

    def test_frozen_producer_receipt_and_every_input_byte(self):
        raw = (FIXTURES / "producer-receipt.json").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), RECEIPT_SHA256)
        receipt = json.loads(raw)
        self.assertEqual(receipt["producer_commit"], PRODUCER)
        self.assertEqual(tuple(receipt["axiom_version"]), PRE_DECOUPLING)
        self.assertEqual(hashlib.sha256((FIXTURES / "producer.py").read_bytes()).hexdigest(),
                         receipt["script_sha256"])
        for name, expected in receipt["fixtures"].items():
            with self.subTest(name=name):
                content = (FIXTURES / name).read_bytes()
                self.assertEqual(len(content), expected["bytes"])
                self.assertEqual(hashlib.sha256(content).hexdigest(), expected["sha256"])

    def test_package_format_generator_and_declared_capabilities_are_unchanged(self):
        self.assertEqual({"schema": modeling.SCHEMA, "profile": modeling.PROFILE,
                          "generator": modeling.GENERATOR, "capabilities": list(modeling.CAPABILITIES)},
                         fixture("model-contract"))

    def test_all_existing_historical_pairs_keep_their_era_and_rebuild(self):
        versions = fixture("historical-versions")
        self.assertIn("PRE_CARD_REFERENCE_AXIOM_VERSIONS", versions)
        self.assertEqual(modeling.PRE_DECOUPLING_AXIOM_VERSIONS, frozenset({PRE_DECOUPLING}))
        original = json.loads((ROOT / "tests/fixtures/model-package-main-a393a0f0.json").read_bytes())
        # Synthetic version probes test the exact allowlist. The original frozen
        # a393a0f0 fixture is left intact; these are not claimed as producer outputs.
        for name, pairs in versions.items():
            self.assertEqual(getattr(modeling, name), frozenset(map(tuple, pairs)), name)
            for pair in pairs:
                with self.subTest(era=name, version=pair):
                    package = deepcopy(original)
                    package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = pair
                    supplied = deepcopy(package)
                    rebuilt = verify_package(package)
                    expected = deepcopy(package)
                    expected["manifest"]["axiom_revision"] = modeling.AXIOM_REVISION
                    expected["manifest"]["axiom_sha256"] = modeling.AXIOM_SHA256
                    self.assertEqual(rebuilt, expected)
                    self.assertEqual(package, supplied)

    def test_pre_adoption_section_profile_rebuilds_material_and_reference_meshes(self):
        rebuilt = self.assert_rebuild_only_updates_axiom_version("profile")
        objects = rebuilt["derived"]["objects"]
        self.assertEqual(len(objects), 4)
        self.assertEqual(sorted(int(obj["volume_mm3"]) for obj in objects),
                         [2138400, 2138400, 2138400, 84960000])
        self.assertEqual(sum(obj["role"] == "reference" for obj in objects), 1)

    def test_pre_adoption_finite_grid_preserves_full_definitions_and_hole(self):
        rebuilt = self.assert_rebuild_only_updates_axiom_version("finite-grid")
        self.assertIn("u series 100 100 3", rebuilt["definitions"]["base_scene"])
        self.assertIn("grid 0 on 1 from-system 0 origin 0 0", rebuilt["definitions"]["base_scene"])
        self.assertEqual(rebuilt["derived"]["objects"][0]["volume_mm3"], "1171200000")

    def test_pre_adoption_infinite_grid_preserves_signed_indices_and_vertex_keys(self):
        rebuilt = self.assert_rebuild_only_updates_axiom_version("infinite-grid")
        for token in ("next-key 9", "vertex-key 1 cell -2 1 anchor 1 2 1 2", "grid 0 on 1 from-binding 0"):
            self.assertIn(token, rebuilt["definitions"]["base_scene"])
        self.assertEqual(rebuilt["derived"]["objects"][0]["volume_mm3"], "1171200000")

    def test_pre_adoption_stagger_preserves_negative_band_and_exact_timber_geometry(self):
        rebuilt = self.assert_rebuild_only_updates_axiom_version("stagger")
        self.assertIn("v repeat 0 1830 stagger 400", rebuilt["definitions"]["base_scene"])
        self.assertIn("at-line grid 10 v 1 band -1", rebuilt["definitions"]["base_scene"])
        obj = rebuilt["derived"]["objects"][0]
        self.assertEqual(obj["volume_mm3"], "1746360")
        self.assertEqual(sorted({point[1] for point in obj["vertices_mm"]}), [1817, 1844])

    def test_pre_adoption_parameters_preserve_reference_instead_of_evaluated_literal(self):
        rebuilt = self.assert_rebuild_only_updates_axiom_version("parameter")
        self.assertIn("v repeat 0 param:1:1", rebuilt["definitions"]["base_scene"])
        self.assertIn("parameters/1", rebuilt["manifest"]["capabilities"])
        self.assertEqual(rebuilt["derived"]["objects"][0]["volume_mm3"], "1746360")
        self.assertEqual(sorted({point[1] for point in rebuilt["derived"]["objects"][0]["vertices_mm"]}),
                         [1817, 1844], "the preserved parameter must actually determine this timber's line")

    def test_subdivision_input_keeps_the_baseline_capability_refusal(self):
        rejected = fixture("subdivision-rejected")
        original = deepcopy(rejected)
        with self.assertRaises(ModelError) as caught:
            build_package(**rejected["input"])
        self.assertEqual(caught.exception.as_dict(), rejected["expected"])
        self.assertEqual((caught.exception.status, caught.exception.code, caught.exception.clause),
                         ("UNSUPPORTED", "CAPABILITY", "I32"))
        self.assertEqual(rejected, original)

    def test_pre_adoption_version_does_not_gain_unsupported_source_capabilities(self):
        package = fixture("infinite-grid")
        # This is an explicitly altered package, not a frozen successful producer.
        package["definitions"] = deepcopy(fixture("subdivision-rejected")["input"]["definitions"])
        package["manifest"]["source_sha256"] = digest(package["definitions"])
        original = deepcopy(package)
        with self.assertRaises(ModelError) as caught:
            verify_package(package)
        self.assertEqual((caught.exception.status, caught.exception.code, caught.exception.clause),
                         ("UNSUPPORTED", "CAPABILITY", "I32"))
        self.assertEqual(package, original)

    def test_all_six_capability_era_gates_still_reject_earlier_claims(self):
        cases = (("profile", modeling.PRE_SECTION_PROFILE_AXIOM_VERSIONS),
                 ("subdivision", modeling.PRE_SUBDIVISION_AXIOM_VERSIONS),
                 ("stagger", modeling.PARAMETER_AXIOM_VERSIONS),
                 ("parameter", modeling.INFINITE_GRID_AXIOM_VERSIONS),
                 ("infinite-grid", modeling.FINITE_GRID_AXIOM_VERSIONS),
                 ("finite-grid", modeling.ENGINEERING_AXIOM_VERSIONS))
        for name, versions in cases:
            for version in versions:
                with self.subTest(source=name, version=version):
                    package = fixture("infinite-grid" if name == "subdivision" else name)
                    if name == "subdivision":
                        package["definitions"] = deepcopy(fixture("subdivision-rejected")["input"]["definitions"])
                        package["manifest"]["source_sha256"] = digest(package["definitions"])
                    package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = version
                    self.assert_version_rejection(package)

    def test_unknown_and_crossed_axiom_pairs_cannot_enter_replay(self):
        old_revision, old_hash = PRE_DECOUPLING
        current_revision, current_hash = modeling.AXIOM_REVISION, modeling.AXIOM_SHA256
        previous_revision, previous_hash = next(iter(modeling.PRE_CARD_REFERENCE_AXIOM_VERSIONS))
        for version in (("0" * 40, "0" * 64), ("0" * 40, old_hash), (old_revision, "0" * 64),
                        (old_revision, current_hash), (current_revision, old_hash),
                        (old_revision, previous_hash), (previous_revision, old_hash)):
            with self.subTest(version=version):
                package = fixture("profile")
                package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = version
                self.assert_version_rejection(package)

    def test_rehashing_false_geometry_does_not_bypass_actual_reconstruction(self):
        package = fixture("finite-grid")
        package["derived"]["objects"][0]["vertices_mm"][0][0] += 1
        package["manifest"]["geometry_sha256"] = digest(package["derived"])
        original = deepcopy(package)
        with self.assertRaises(ModelError) as caught:
            verify_package(package)
        self.assertEqual((caught.exception.status, caught.exception.code, caught.exception.clause),
                         ("INVALID", "SNAPSHOT_MISMATCH", "I31"))
        self.assertEqual(package, original)

    def test_rehashing_changed_source_does_not_accept_the_old_geometry(self):
        package = fixture("finite-grid")
        source = package["definitions"]["base_scene"]
        self.assertIn("spec far 120\n", source)
        package["definitions"]["base_scene"] = source.replace("spec far 120\n", "spec far 121\n")
        package["manifest"]["source_sha256"] = digest(package["definitions"])
        original = deepcopy(package)
        with self.assertRaises(ModelError) as caught:
            verify_package(package)
        self.assertEqual((caught.exception.status, caught.exception.code, caught.exception.clause),
                         ("INVALID", "SNAPSHOT_MISMATCH", "I31"))
        self.assertEqual(package, original)


if __name__ == "__main__":
    unittest.main()
