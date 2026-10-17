"""Engineering capability boundaries and exact known-axiom compatibility."""
from copy import deepcopy
import base64
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
import modeling
from modeling import ModelError, ModelWorld, build_package, verify_package
from modeling.base import load_base
from modeling.common import canonical_bytes, digest, scene_required_capabilities

LEGACY_VERSION = ("494660068ceb884c1a96884a2b704e3bcf5d24ca", "bc01cf0db266f97255156e28e40fb235833031fb95f1f234ad6d90a9f08240f8")
ENGINEERING_VERSION = ("5698f8501d539ed3a6f0644dab854e62e3bafb1a", "1843e3e9f6a3a6db07ceaa8f62fad693039296d519791af98c2a433554308bcf")
FINITE_GRID_VERSION = ("b4fe75f7f03ed81b4bc9f85a044282f91bd27cb6", "2d31868524cb2776c2c405367fa69087b8f43371f320f12f3405fb14ce9fdf28")
CLARIFIED_MAIN_VERSION = ("a393a0f01284433ca20fe8b10d9f21111026e7f1", "b06ffecf4f3b7a907a50d329f2073799d9514daa26b9056380f62ad37e5725ee")
K3_MAIN_VERSION = ('d1db88ae99ca9b6858b0ada34d082e902f00c9f9', '9d4f90aacbc863941c1065a6b962f760e7e842c4d7dda55a56c4dc321f9a0f93')
PRE_CARD_REFERENCE_MAIN_VERSION = ("651c661b2c4c224c58bb4a2ed0a42ed929a16aa6", "ab31dc36d5416762ac44932940a94f6142b72e831ceb62c0bc67375512109004")
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

    def saved_main_package(self):
        # Unmodified build_package output from main 2004c6c; see fixture provenance.
        package = json.loads((ROOT / "tests/fixtures/model-package-main-a393a0f0.json").read_bytes())
        manifest = package["manifest"]
        self.assertEqual((manifest["axiom_revision"], manifest["axiom_sha256"]),
                         CLARIFIED_MAIN_VERSION)
        return package

    def test_released_main_package_reopens_and_rebuilds_geometry(self):
        package = self.saved_main_package()
        original = deepcopy(package)
        try:
            rebuilt = verify_package(package)
        except ModelError as exc:
            self.fail("released main package must reopen and rebuild: "
                      f"{exc.status}/{exc.code} ({exc.clause})")
        self.assertEqual(package, original, "opening must preserve the saved package")
        for key in ("definitions", "request", "derived"):
            self.assertEqual(rebuilt[key], original[key], key)
        self.assertEqual(rebuilt["manifest"]["geometry_sha256"],
                         original["manifest"]["geometry_sha256"])
        self.assertEqual(rebuilt["manifest"]["capabilities"],
                         original["manifest"]["capabilities"])
        self.assertEqual(rebuilt["manifest"]["axiom_revision"], modeling.AXIOM_REVISION)
        self.assertNotIn("identity-ledger/1", rebuilt["manifest"]["capabilities"])

    def test_released_k3_profile_package_reopens_and_rebuilds_geometry(self):
        # Unmodified build_package output from released main caf49852.
        package = json.loads((ROOT / "tests/fixtures/model-package-main-d1db88ae-profile.json").read_bytes())
        manifest = package["manifest"]
        self.assertEqual((manifest["axiom_revision"], manifest["axiom_sha256"]), K3_MAIN_VERSION)
        self.assertIn("section-profile/1", manifest["capabilities"])
        self.assertIn("requires section-profile/1", package["definitions"]["base_scene"])
        original = deepcopy(package)
        try:
            rebuilt = verify_package(package)
        except ModelError as exc:
            self.fail("released K3 profile package must reopen and rebuild: "
                      f"{exc.status}/{exc.code} ({exc.clause})")
        self.assertEqual(package, original, "opening must preserve the saved K3 package")
        for key in ("definitions", "request", "derived"):
            self.assertEqual(rebuilt[key], original[key], key)
        for key in ("geometry_sha256", "capabilities"):
            self.assertEqual(rebuilt["manifest"][key], original["manifest"][key], key)
        self.assertEqual(rebuilt["manifest"]["axiom_revision"], modeling.AXIOM_REVISION)
        self.assertEqual(rebuilt["manifest"]["axiom_sha256"], modeling.AXIOM_SHA256)
        self.assertNotIn("identity-ledger/1", rebuilt["manifest"]["capabilities"])
        for version in ((K3_MAIN_VERSION[0], modeling.AXIOM_SHA256),
                        (modeling.AXIOM_REVISION, K3_MAIN_VERSION[1])):
            altered = deepcopy(package)
            altered["manifest"]["axiom_revision"], altered["manifest"]["axiom_sha256"] = version
            with self.subTest(version=version), self.assertRaises(ModelError) as caught:
                verify_package(altered)
            self.assertEqual(caught.exception.code, "AXIOM_VERSION")

    def saved_pre_card_reference_package(self):
        # Frozen, unmodified build_package output from main 839063b9; see provenance.
        raw = (ROOT / "tests/fixtures/model-package-main-839063b9-profile.json").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         "c83643807a10bf580998508ffff0dd45a99d594a97183242ea30bb56359e34aa")
        package = json.loads(raw)
        manifest = package["manifest"]
        self.assertEqual((manifest["axiom_revision"], manifest["axiom_sha256"]),
                         PRE_CARD_REFERENCE_MAIN_VERSION)
        self.assertIn("section-profile/1", manifest["capabilities"])
        self.assertIn("requires section-profile/1", package["definitions"]["base_scene"])
        return package

    def test_released_pre_card_reference_package_reopens_and_only_updates_axiom_version(self):
        package = self.saved_pre_card_reference_package()
        original = deepcopy(package)
        try:
            rebuilt = verify_package(package)
        except ModelError as exc:
            self.fail("released pre-card-reference package must reopen and rebuild: "
                      f"{exc.status}/{exc.code} ({exc.clause})")
        self.assertEqual(package, original, "opening must preserve the saved package")
        self.assertNotEqual(original["manifest"]["axiom_revision"], modeling.AXIOM_REVISION)
        self.assertNotEqual(original["manifest"]["axiom_sha256"], modeling.AXIOM_SHA256)
        expected = deepcopy(original)
        expected["manifest"]["axiom_revision"] = modeling.AXIOM_REVISION
        expected["manifest"]["axiom_sha256"] = modeling.AXIOM_SHA256
        self.assertEqual(rebuilt, expected,
                         "rebuild may change only axiom_revision and axiom_sha256")

    def test_pre_card_reference_package_rejects_unknown_and_mixed_axiom_versions(self):
        package = self.saved_pre_card_reference_package()
        revision, sha256 = PRE_CARD_REFERENCE_MAIN_VERSION
        for version in (("0" * 40, "0" * 64), ("0" * 40, sha256),
                        (revision, "0" * 64), (revision, modeling.AXIOM_SHA256),
                        (modeling.AXIOM_REVISION, sha256),
                        (revision, K3_MAIN_VERSION[1]), (K3_MAIN_VERSION[0], sha256)):
            altered = deepcopy(package)
            altered["manifest"]["axiom_revision"], altered["manifest"]["axiom_sha256"] = version
            with self.subTest(version=version), self.assertRaises(ModelError) as caught:
                verify_package(altered)
            self.assertEqual(caught.exception.code, "AXIOM_VERSION")
        self.assertEqual(package, self.saved_pre_card_reference_package())

    def pre_card_reference_versions(self):
        # Accepted minus current minus the post-adoption pairs (GEO-261 retired b3c79615,
        # which already contains D64/I74/R60); shared with the verifier itself.
        current = (modeling.AXIOM_REVISION, modeling.AXIOM_SHA256)
        return sorted(modeling._pre_card_reference_versions(current))

    def assert_card_requires_adopted_axioms(self, package, label):
        original = deepcopy(package)
        for version in self.pre_card_reference_versions():
            altered = deepcopy(package)
            altered['manifest']['axiom_revision'], altered['manifest']['axiom_sha256'] = version
            with self.subTest(version=version, path=label):
                with self.assertRaises(ModelError, msg=label) as caught:
                    verify_package(altered)
                self.assertEqual(caught.exception.code, 'AXIOM_VERSION', label)
                self.assertEqual(caught.exception.status, 'UNSUPPORTED', label)
                self.assertIn('grid-card-reference/1', caught.exception.message, label)
                self.assertEqual(altered['definitions'], original['definitions'],
                                 label + ': reject must not rewrite source')
        self.assertEqual(package, original)

    def test_pre_card_axioms_reject_manifest_card_capability(self):
        package = self.build()
        package['manifest']['capabilities'].append('grid-card-reference/1')
        self.assert_card_requires_adopted_axioms(package, 'CARD_AXIOM_MANIFEST')

    def test_pre_card_axioms_reject_scene_card_capability_before_rebuild(self):
        package = self.build()
        package['definitions']['base_scene'] += 'requires grid-card-reference/1\n'
        package['manifest']['source_sha256'] = digest(package['definitions'])
        self.assert_card_requires_adopted_axioms(package, 'CARD_AXIOM_SOURCE')

    def card_reference_package(self):
        definitions = deepcopy(CASE['definitions'])
        def encoded(value):
            return base64.b64encode(canonical_bytes(value)).decode('ascii')
        lines = ['requires parameters/1', 'parameters begin',
                 'parameters card ' + encoded({'id': 10, 'name': 'P', 'nextFieldId': 9})]
        for identifier, value in ((3, '12'), (8, '30')):
            lines.append('parameters field ' + encoded({
                'parameterId': 10, 'id': identifier, 'name': str(identifier), 'type': 0,
                'expression': {'op': 'literal', 'num': value, 'den': '1', 'unit': 'mm'},
            }))
        lines += ['parameters end', 'requires grid-card-reference/1',
                  'grid-system 4 name-hex 47 main-along none card-reference 10 3 8 u repeat -5 card v repeat 7 card']
        definitions['base_scene'] += '\n'.join(lines) + '\n'
        return build_package(definitions, deepcopy(CASE['request']))

    def test_pre_card_axioms_reject_card_syntax_with_stripped_declarations(self):
        package = self.card_reference_package()
        self.assertEqual(verify_package(package), package, 'CARD_AXIOM_SYNTAX current control')
        package['manifest']['capabilities'].remove('grid-card-reference/1')
        package['definitions']['base_scene'] = package['definitions']['base_scene'].replace(
            'requires grid-card-reference/1\n', '')
        package['manifest']['source_sha256'] = digest(package['definitions'])
        self.assert_card_requires_adopted_axioms(package, 'CARD_AXIOM_SYNTAX')

    def test_adopted_card_axioms_roundtrip_current_capability_and_sources(self):
        package = self.card_reference_package()
        self.assertIn('grid-card-reference/1', package['manifest']['capabilities'])
        self.assertIn('card-reference 10 3 8', package['definitions']['base_scene'])
        self.assertEqual((package['manifest']['axiom_revision'], package['manifest']['axiom_sha256']),
                         (modeling.AXIOM_REVISION, modeling.AXIOM_SHA256))
        self.assertEqual(verify_package(package), package, 'CARD_AXIOM_CURRENT')

    def card_claim_fixture(self):
        # Untouched a898ad6e producer output at b3c79615 (the D64 adoption, now
        # PRE_DECOUPLING); appending the card claim is a deliberate probe.
        package = json.loads((ROOT / 'tests/fixtures/domain-decoupling-main-a898ad6e/parameter.json').read_bytes())
        package['manifest']['capabilities'].append('grid-card-reference/1')
        return package

    def test_card_axiom_era_partition_matches_the_frozen_pre_adoption_allowlist(self):
        current = (modeling.AXIOM_REVISION, modeling.AXIOM_SHA256)
        accepted, pre = modeling._accepted_axiom_versions(current), modeling._pre_card_reference_versions(current)
        # a898ad6e pinned the D64 adoption itself, so its frozen noncurrent families are
        # exactly the versions older than D64/I74/R60 (an independent oracle).
        frozen = json.loads((ROOT / 'tests/fixtures/domain-decoupling-main-a898ad6e/historical-versions.json').read_bytes())
        self.assertEqual(frozenset(tuple(pair) for pairs in frozen.values() for pair in pairs), pre, 'CARD_AXIOM_ERA')
        self.assertEqual(modeling.PRE_DECOUPLING_AXIOM_VERSIONS, modeling.CARD_REFERENCE_AXIOM_VERSIONS, 'CARD_AXIOM_ERA')
        self.assertEqual(accepted, pre | modeling.CARD_REFERENCE_AXIOM_VERSIONS | {current}, 'CARD_AXIOM_ERA')
        self.assertFalse(pre & modeling.CARD_REFERENCE_AXIOM_VERSIONS, 'CARD_AXIOM_ERA')
        self.assertNotIn(current, pre, 'CARD_AXIOM_ERA')

    def test_card_claims_split_exactly_at_the_d64_adoption_before_rebuild(self):
        class Reached(Exception):
            pass
        current = (modeling.AXIOM_REVISION, modeling.AXIOM_SHA256)
        with mock.patch.object(modeling, 'build_package', side_effect=Reached):
            for version in sorted(modeling._pre_card_reference_versions(current)):
                package = self.card_claim_fixture()
                package['manifest']['axiom_revision'], package['manifest']['axiom_sha256'] = version
                with self.subTest(version=version):
                    try:
                        verify_package(package)
                    except ModelError as error:
                        self.assertEqual(('UNSUPPORTED', 'AXIOM_VERSION'), (error.status, error.code), 'CARD_AXIOM_ERA')
                        self.assertIn('grid-card-reference/1', error.message, 'CARD_AXIOM_ERA')
                    except Reached:
                        self.fail('CARD_AXIOM_ERA: pre-D64 card claim reached the rebuild')
                    else:
                        self.fail('CARD_AXIOM_ERA: pre-D64 card claim was accepted')
            # The frozen producer's own pair is the D64 adoption: its card claim is not refused.
            package = self.card_claim_fixture()
            try:
                verify_package(package)
            except Reached:
                pass
            except ModelError as error:
                self.fail('CARD_AXIOM_ERA: post-adoption card claim was refused: ' + json.dumps(error.as_dict()))
            else:
                self.fail('CARD_AXIOM_ERA: rebuild was not reached')

    def test_post_adoption_previous_revision_card_package_rebuilds(self):
        package = self.card_reference_package()
        package['manifest']['axiom_revision'], package['manifest']['axiom_sha256'] = next(iter(modeling.CARD_REFERENCE_AXIOM_VERSIONS))
        supplied = deepcopy(package)
        rebuilt = verify_package(package)
        expected = deepcopy(supplied)
        expected['manifest']['axiom_revision'], expected['manifest']['axiom_sha256'] = modeling.AXIOM_REVISION, modeling.AXIOM_SHA256
        self.assertEqual(expected, rebuilt, 'CARD_AXIOM_ERA: b3c79615 already defines D64/I74/R60')
        self.assertEqual(supplied, package, 'CARD_AXIOM_ERA: verification must not upgrade provenance in place')

    def test_pre_card_axioms_ignore_card_words_in_source_comments(self):
        package = self.build()
        definitions = deepcopy(package['definitions'])
        definitions['base_scene'] += '# requires grid-card-reference/1 card-reference card\n'
        package = build_package(definitions, deepcopy(CASE['request']))
        self.assertNotIn('grid-card-reference/1', package['manifest']['capabilities'])
        for version in self.pre_card_reference_versions():
            altered = deepcopy(package)
            altered['manifest']['axiom_revision'], altered['manifest']['axiom_sha256'] = version
            with self.subTest(version=version):
                self.assertEqual(verify_package(altered)['derived'], package['derived'],
                                 'CARD_AXIOM_COMMENT: older sources without capability remain supported')

    def test_released_main_package_rejects_rehashed_false_geometry(self):
        package = self.saved_main_package()
        package["derived"]["objects"][0]["vertices_mm"][0][0] += 1
        package["manifest"]["geometry_sha256"] = digest(package["derived"])
        with self.assertRaises(ModelError) as caught:
            verify_package(package)
        self.assertEqual(caught.exception.code, "SNAPSHOT_MISMATCH")

    def test_released_main_package_does_not_gain_identity_capability(self):
        package = self.saved_main_package()
        package["definitions"]["base_scene"] += "requires identity-ledger/1\n"
        package["manifest"]["source_sha256"] = digest(package["definitions"])
        with self.assertRaises(ModelError) as caught:
            verify_package(package)
        self.assertEqual(caught.exception.code, "CAPABILITY")

    def test_released_main_revision_requires_its_exact_hash_pair(self):
        for version in ((CLARIFIED_MAIN_VERSION[0], modeling.AXIOM_SHA256),
                        (modeling.AXIOM_REVISION, CLARIFIED_MAIN_VERSION[1])):
            package = self.saved_main_package()
            package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = version
            with self.subTest(version=version), self.assertRaises(ModelError) as caught:
                verify_package(package)
            self.assertEqual(caught.exception.code, "AXIOM_VERSION")

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

    def test_exact_pre_generation_revision_still_rebuilds_existing_package(self):
        package=self.build();package['manifest']['axiom_revision'],package['manifest']['axiom_sha256']=next(iter(modeling.PRE_GENERATION_AXIOM_VERSIONS))
        self.assertEqual(package['derived'],verify_package(package)['derived'])

    def test_generation_sources_are_gated_before_unsupported_model_adapter_runs(self):
        for scene in ['requires assembly-timber-generation/1\n','owned 1 1 timber 1 27 33 role primary\n']:
            self.assertIn('assembly-timber-generation/1',scene_required_capabilities(scene))
            with self.assertRaises(ModelError) as caught:load_base(scene,executable='must-not-execute')
            self.assertEqual('CAPABILITY',caught.exception.code)

    def test_unknown_revision_or_mixed_revision_hash_pair_is_rejected(self):
        for version in [("0" * 40, LEGACY_VERSION[1]), (LEGACY_VERSION[0], "0" * 64),
                        ("0" * 40, "0" * 64), (LEGACY_VERSION[0], modeling.AXIOM_SHA256),
                        (modeling.AXIOM_REVISION, LEGACY_VERSION[1]),
                        (ENGINEERING_VERSION[0], modeling.AXIOM_SHA256),
                        (modeling.AXIOM_REVISION, ENGINEERING_VERSION[1]),
                        (ENGINEERING_VERSION[0], LEGACY_VERSION[1])]:
            package = self.build()
            package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = version
            with self.subTest(version=version), self.assertRaises(ModelError) as caught:
                verify_package(package)
            self.assertEqual(caught.exception.code, "AXIOM_VERSION")

    def test_exact_previous_engineering_package_retains_real_material_sources(self):
        material = {"id": "panel-a", "version": 1, "kind": "panel", "name": "面材",
                    "width": 915, "length": 1830, "thickness": "6.50", "notes": None}
        record = {"value": material, "fingerprint": digest(material)}
        definitions = deepcopy(CASE["definitions"])
        definitions["base_scene"] += "requires engineering-spec/1\nengineering material " + base64.b64encode(canonical_bytes(record)).decode() + "\n"
        package = build_package(definitions, deepcopy(CASE["request"]))
        package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = ENGINEERING_VERSION
        original = deepcopy(package)
        rebuilt = verify_package(package)
        self.assertEqual(package, original)
        self.assertIn(ENGINEERING_VERSION, modeling.ENGINEERING_AXIOM_VERSIONS)
        self.assertNotIn(ENGINEERING_VERSION, modeling.LEGACY_AXIOM_VERSIONS)
        self.assertIn("engineering-spec/1", rebuilt["manifest"]["capabilities"])
        for key in ("definitions", "request", "derived"):
            self.assertEqual(rebuilt[key], original[key])
        package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = LEGACY_VERSION
        with self.assertRaises(ModelError) as caught:
            verify_package(package)
        self.assertEqual(caught.exception.code, "AXIOM_VERSION")

    def test_finite_grid_sources_roundtrip_but_reject_pre_grid_axioms(self):
        definitions = deepcopy(CASE["definitions"])
        definitions["base_scene"] += ("grid-system 0 name-hex e585b1e794a8 main-along none u series 100 100 3 v none\n"
                                      "grid 0 on 1 from-system 0 origin 0 0\n")
        package = build_package(definitions, deepcopy(CASE["request"]))
        rebuilt = verify_package(package)
        self.assertEqual(rebuilt["definitions"], package["definitions"])
        self.assertEqual(rebuilt["derived"], package["derived"])
        self.assertIn("grid-system 0 name-hex", rebuilt["definitions"]["base_scene"])
        self.assertIn("grid 0 on 1 from-system 0 origin 0 0", rebuilt["definitions"]["base_scene"])
        previous = deepcopy(package)
        previous["manifest"]["axiom_revision"], previous["manifest"]["axiom_sha256"] = FINITE_GRID_VERSION
        original = deepcopy(previous)
        old_rebuilt = verify_package(previous)
        self.assertEqual(previous, original, "verification cannot silently upgrade a saved finite package")
        self.assertEqual(old_rebuilt["definitions"], original["definitions"])
        self.assertEqual(old_rebuilt["derived"], original["derived"])
        self.assertIn("u series 100 100 3", old_rebuilt["definitions"]["base_scene"])
        for version in (LEGACY_VERSION, ENGINEERING_VERSION):
            old = deepcopy(package)
            old["manifest"]["axiom_revision"], old["manifest"]["axiom_sha256"] = version
            with self.subTest(version=version), self.assertRaises(ModelError) as caught:
                verify_package(old)
            self.assertEqual(caught.exception.code, "AXIOM_VERSION")

    def test_old_revision_gate_cannot_hide_new_syntax_by_removing_definition(self):
        package = self.build()
        for version in (LEGACY_VERSION, ENGINEERING_VERSION):
            for source in ("grid 0 on 1 from-system 0 origin 0 0\n",
                           "\ufeffgrid-system 0 name-hex 61 main-along none u 0 v none\n",
                           "canvas-pos grid-system 0 0 0\n"):
                bad = deepcopy(package)
                bad["manifest"]["axiom_revision"], bad["manifest"]["axiom_sha256"] = version
                bad["definitions"]["base_scene"] = source + bad["definitions"]["base_scene"]
                bad["manifest"]["source_sha256"] = digest(bad["definitions"])
                with self.subTest(version=version, source=source), self.assertRaises(ModelError) as caught:
                    verify_package(bad)
                self.assertEqual(caught.exception.code, "AXIOM_VERSION")

    def test_known_finite_revision_cannot_claim_any_infinite_or_vertex_key_syntax(self):
        package = self.build()
        syntaxes = [
            "grid-system 0 name-hex 61 main-along none u repeat 0 600 v repeat 0 400\n",
            "grid-system 0 name-hex 61 main-along none u repeat-panel 600 gap 3 from 0 v none\n",
            "grid-binding 0 on-boundary 1 from-system 0 vertex-key 1 cell -2 1 anchor 0 1 0 1\n",
            "boundary-keyed 1 geometry-hash " + "0" * 64 + " outline 1:0,0 2:100,0 3:100,100 4:0,100\n",
            "boundary-vertex-keys 1 outer 1 2 3 4 next-key 5\n",
            "grid 0 on 1 from-binding 0\n",
            "subgrid 1 parent 0 lattice-cell -2 1 divisions u 2 v 2\n",
            "canvas-pos grid-binding 0 10 20\n",
        ]
        for source in syntaxes:
            bad = deepcopy(package)
            bad["manifest"]["axiom_revision"], bad["manifest"]["axiom_sha256"] = FINITE_GRID_VERSION
            bad["definitions"]["base_scene"] = source + bad["definitions"]["base_scene"]
            bad["manifest"]["source_sha256"] = digest(bad["definitions"])
            with self.subTest(source=source), self.assertRaises(ModelError) as caught:
                verify_package(bad)
            self.assertEqual(caught.exception.code, "AXIOM_VERSION")

    def test_current_infinite_binding_package_keeps_signed_indices_and_vertex_keys(self):
        definitions = deepcopy(CASE["definitions"])
        definitions["base_scene"] += (
            "boundary-vertex-keys 1 outer 1 2 3 4 hole 5 6 7 8 next-key 9\n"
            "grid-system 0 name-hex e784a1e99990 main-along none u repeat 0 600 v repeat 0 400\n"
            "grid-binding 0 on-boundary 1 from-system 0 vertex-key 1 cell -2 1 anchor 1 2 1 2\n"
            "grid 0 on 1 from-binding 0\n"
        )
        package = build_package(definitions, deepcopy(CASE["request"]))
        original = deepcopy(package)
        rebuilt = verify_package(package)
        self.assertEqual(original, package)
        self.assertEqual(rebuilt["definitions"], original["definitions"])
        self.assertEqual(rebuilt["derived"], original["derived"])
        scene = rebuilt["definitions"]["base_scene"]
        for text in ("next-key 9", "vertex-key 1 cell -2 1 anchor 1 2 1 2", "grid 0 on 1 from-binding 0"):
            self.assertIn(text, scene)

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


class StaggerModelCompatibility(unittest.TestCase):
    """Exercise the real native adapter before granting the D10b axiom version."""
    def scene(self, delta="400", band=0):
        # Move the carrier into the chosen unshifted u band. The v binding is
        # anchored at an even band so its translation is independent of delta.
        lo, hi = band * 2000, (band + 1) * 2000
        stagger = "" if delta is None else " stagger " + delta
        return (f"surface 1 origin 0 0 0 u +x v +y outline {lo},0 {hi},0 {hi},4000 {lo},4000\n"
                "boundary-vertex-keys 1 outer 1 2 3 4 next-key 5\n"
                f"grid-system 0 name-hex 61 main-along none u repeat 0 2000 v repeat 0 1830{stagger}\n"
                f"grid-binding 0 on-boundary 1 from-system 0 vertex-key 1 cell {band} 0 anchor 0 1 0 1\n"
                "grid 10 on 1 from-binding 0\n"
                "timber 90 20 33 role boundary\nplace 90 on 1 at-face e3 +v +n\n"
                "timber 91 20 33 role boundary\nplace 91 on 1 at-face e1 +v +n\n"
                "timber 1 27 33 role primary\n"
                f"place 1 on 1 at-line grid 10 v 1" + (f" band {band}" if delta is not None else "") + " +u +n\n")

    def definitions(self, scene):
        return {"base_scene": scene, "extensions": []}

    def request(self):
        return {"roots": [{"kind": "timber", "id": 1}], "role": "geometry", "target": "solid-set", "allow_partial": False}

    def build(self, scene=None):
        return build_package(self.definitions(scene or self.scene()), self.request())

    def test_actual_adapter_preserves_stagger_band_and_exact_mesh_roundtrip(self):
        for band in (-2, -1, 0, 1, 2):
            with self.subTest(band=band):
                package = self.build(self.scene(band=band))
                source = package["definitions"]["base_scene"]
                self.assertIn("v repeat 0 1830 stagger 400", source)
                self.assertIn(f"at-line grid 10 v 1 band {band}", source)
                # Binding follows the same odd-band offset, canceling it at
                # the anchored boundary; the local line remains at v=1830.
                obj = package["derived"]["objects"][0]
                self.assertEqual(obj["volume_mm3"], str(1960 * 27 * 33))
                self.assertEqual(sorted({p[1] for p in obj["vertices_mm"]}), [1817, 1844])
                original = deepcopy(package)
                rebuilt = verify_package(json.loads(json.dumps(package)))
                self.assertEqual(package, original)
                self.assertEqual(rebuilt, package)

    def test_adapter_rejects_literal_zero_multiples_missing_extra_and_outside_band(self):
        sources = [self.scene(delta=v) for v in ("0", "-0", "1830", "-3660")]
        sources += [self.scene().replace(" band 0 +u", " +u"),
                    self.scene(None).replace("v 1 +u", "v 1 band 0 +u"),
                    self.scene().replace("band 0 +u", "band 1 +u"),
                    self.scene() + "subgrid 11 parent 10 lattice-cell 0 0 divisions u 2 v 2\n"]
        for source in sources:
            with self.subTest(source=source), self.assertRaises(ModelError) as caught:
                self.build(source)
            self.assertEqual(caught.exception.status, "INVALID")

    def test_blank_is_unset_and_negative_offset_stays_exact(self):
        plain = self.build(self.scene(None))
        self.assertNotIn("stagger", plain["definitions"]["base_scene"])
        self.assertNotIn("band", plain["definitions"]["base_scene"])
        negative = self.build(self.scene("-400"))
        self.assertIn("stagger -400", verify_package(negative)["definitions"]["base_scene"])

    def test_parameter_stagger_preserves_reference_and_rejects_evaluated_zero(self):
        def record(kind, value):
            return "parameters " + kind + " " + base64.b64encode(canonical_bytes(value)).decode() + "\n"
        for value in ("400", "-400", "0", "1830"):
            parameters = ("requires parameters/1\nparameters begin\n" +
                          record("card", {"id": 1, "name": "Phase", "nextFieldId": 2}) +
                          record("field", {"parameterId": 1, "id": 1, "name": "delta", "type": 0,
                                           "expression": {"op": "literal", "num": value, "den": "1", "unit": "mm"}}) +
                          "parameters end\n")
            source = parameters + self.scene("param:1:1")
            with self.subTest(value=value):
                if value in ("0", "1830"):
                    with self.assertRaises(ModelError) as caught:
                        self.build(source)
                    self.assertEqual(caught.exception.status, "INVALID")
                else:
                    package = self.build(source)
                    self.assertIn("stagger param:1:1", package["definitions"]["base_scene"])
                    self.assertIn("parameters/1", package["manifest"]["capabilities"])
                    self.assertEqual(verify_package(package), package)

    def test_engineering_example_space_preview_retains_all_seven_timbers(self):
        sys.path.insert(0, str(ROOT / "geometry-web"))
        from space_modeling import preview
        with zipfile.ZipFile(ROOT / "geometry-web/examples/engineering-spec-v1.gcanvas") as archive:
            manifest = json.loads(archive.read("manifest.json"))
        model = manifest["models"][0]
        source = deepcopy(model["input"])
        result = preview(source)
        self.assertEqual(source, model["input"])
        self.assertEqual(result["summary"]["timber_volume_mm3"], "18494487")
        self.assertEqual(len(result["timbers"]["derived"]["objects"]), 7)
        for key in ("space", "volume", "clearance", "timbers"):
            self.assertEqual(verify_package(result[key])["derived"], result[key]["derived"])
            self.assertIn("engineering-spec/1", result[key]["manifest"]["capabilities"])

    def test_known_pre_stagger_package_rebuilds_without_upgrading_input(self):
        for version in modeling.PARAMETER_AXIOM_VERSIONS:
            package = self.build(self.scene(None))
            package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = version
            original = deepcopy(package)
            rebuilt = verify_package(package)
            self.assertEqual(package, original)
            self.assertEqual(rebuilt["derived"], package["derived"])

    def test_all_pre_stagger_versions_reject_stagger_and_band_before_replay(self):
        versions = (modeling.LEGACY_AXIOM_VERSIONS | modeling.ENGINEERING_AXIOM_VERSIONS |
                    modeling.FINITE_GRID_AXIOM_VERSIONS | modeling.INFINITE_GRID_AXIOM_VERSIONS |
                    modeling.PARAMETER_AXIOM_VERSIONS)
        for version in versions:
            for scene in (self.scene(), self.scene().replace(" stagger 400", "")):
                package = self.build()
                package["definitions"]["base_scene"] = "\ufeff" + scene
                package["manifest"]["source_sha256"] = digest(package["definitions"])
                package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = version
                with self.subTest(version=version, scene=scene), self.assertRaises(ModelError) as caught:
                    verify_package(package)
                self.assertEqual(caught.exception.code, "AXIOM_VERSION")

    def test_invalid_stagger_preview_rolls_back_model_world_and_pending_token(self):
        world = ModelWorld(self.definitions(self.scene()), self.request())
        original = world.package
        pending = world.preview(self.definitions(self.scene("-400")))
        with self.assertRaises(ModelError):
            world.preview(self.definitions(self.scene("0")))
        self.assertEqual(world.package, original)
        with self.assertRaises(ModelError) as caught:
            world.confirm(pending["token"])
        self.assertEqual(caught.exception.code, "STALE_PREVIEW")
        fresh = world.preview(self.definitions(self.scene("-400")))
        self.assertIn("stagger -400", world.confirm(fresh["token"])["definitions"]["base_scene"])


if __name__ == "__main__":
    unittest.main()
