"""Q38j-a: native F1 geometry, explicit selection and independent replay.

Expected boxes and quantities below are hand calculations from PROPOSAL Q01.
Only protocol-corruption cases mock the package boundary; normal geometry and
both replay paths execute the fresh native model-base adapter.
"""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "geometry-web", ROOT / "geometry-core"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from tests import binaries
from tests import test_section_profile_modeling as profiles
from modeling import ModelError, canonical_bytes, verify_package
from modeling.base import load_base
import model_update
import scenario_verify
import space_modeling as sm


PREFIX = ("boundary 1 outline 0,0 4000,0 4000,5000 0,5000 kind room_plan\n"
          "placement 1 on boundary 1 origin 0 0 0 u +x v +y\n")
FRAME = {"kind": "advanced", "origin": [1000, 2000, 2700], "N": "+Y", "V": "-Z"}
BOXES = {1: [[1000, 2000, 2667], [1027, 4400, 2700]],
         2: [[1373, 2000, 2667], [1400, 4400, 2700]],
         3: [[1000, 2000, 2450], [1033, 4400, 2477]]}
PROFILE_SUMMARY = {"profile_run_count", "profile_member_count",
                   "profile_material_volume_mm3", "profile_overlap_checked"}


def f1(*, ids=(1,), length=2400, timber=False, copied=False):
    placement = deepcopy(FRAME)
    if copied:
        placement = {"kind": "simple", "dir": "+v", "p": 1000, "q": 2000, "up": "+Z",
                     "host": {"kind": "space-wall-values", "sourceDescription": "SA 頂面取值",
                              "frame": {"origin": [0, 0, 2700], "U": "+X", "V": "+Y", "N": "+Z"},
                              "region": {"outline": [[0, 0], [4000, 0], [4000, 5000], [0, 5000]], "holes": []}}}
    runs = [profiles.run(0, placement=deepcopy(FRAME)),
            profiles.run(1, length=profiles.literal(length), placement=placement),
            profiles.run(2, length=profiles.literal(1000)),
            profiles.run(4, length=profiles.literal(1000),
                         placement={"kind": "advanced", "origin": [1000, 2027, 2700], "N": "+X", "V": "-Z"})]
    prefix = PREFIX
    if timber:
        prefix += "timber 0 27 33 role boundary\nplace 0 on 1 at-face e0 +u +n\n"
    data = {"mode": "plan", "base_scene": profiles.scene(prefix=prefix, runs=runs),
            "placement_id": 1, "obstacles": [],
            "settings": {"bottom": 0, "height": 2700, "edges": [0, 1, 2, 3],
                         "floor": "boundary", "ceiling": "boundary", "holes": "none", "wall_thickness": 100}}
    if ids is not None:
        data["profile_runs"] = [{"kind": "profile-run", "id": identifier} for identifier in ids]
    if timber:
        data["timbers"] = [{"kind": "timber", "id": 0}]
    return data


def saved_record(data, result):
    return {"id": "q38j-a-model", "name": "F1 保存空間", "created_at": "2026-11-02T00:00:00Z",
            "source": {"kind": "scene", "placement_id": 1, "boundary_id": 1,
                       "scene_hash": result["source_sha256"]}, "input": deepcopy(data), "result": deepcopy(result)}


class SpaceProfileRuns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        info = binaries.inspect_one(binaries.BY_NAME["model-base"], path=os.environ.get("GEOMETRY_MODEL_BASE"))
        if info.state != "fresh":
            raise unittest.SkipTest("Set GEOMETRY_MODEL_BASE to a freshly built adapter: " + info.reason)
        cls.base = str(info.path)

    def preview(self, data):
        before = deepcopy(data)
        try:
            return sm.preview(data, base_executable=self.base)
        finally:
            self.assertEqual(data, before, "Q38JA_INPUT_UNCHANGED")

    def reject(self, data, code=None, *, status="INVALID", marker="Q38JA_SELECTION"):
        with self.assertRaises(ModelError, msg=marker) as caught:
            self.preview(data)
        self.assertEqual(caught.exception.status, status, marker)
        if code:
            self.assertEqual(caught.exception.code, code, marker)
        return caught.exception

    def test_q01_exact_native_members_reference_and_material_summary(self):
        data = f1()
        try:
            result = self.preview(data)
        except ModelError as exc:
            self.fail("Q38JA_IMPLEMENTATION: selected native run must build: " + exc.code)
        self.assertEqual(result["schema"], "geometry-space-preview/3", "Q38JA_IMPLEMENTATION")
        self.assertIn("profile_runs", result, "Q38JA_IMPLEMENTATION")
        package = result["profile_runs"]
        self.assertEqual(verify_package(package, base_executable=self.base), package)
        self.assertEqual(package["definitions"], {"base_scene": load_base(data["base_scene"], executable=self.base)["base_scene"], "extensions": []})
        self.assertEqual(package["request"], {"roots": [{"kind": "profile-run", "id": 1}], "role": "geometry", "target": "solid-set", "allow_partial": False})
        self.assertEqual(package["derived"]["status"], "COMPLETE")
        objects = package["derived"]["objects"]
        self.assertEqual(len(objects), 4)
        envelopes = [o for o in objects if o["role"] == "reference"]
        self.assertEqual(len(envelopes), 1, "Q38JA_ENVELOPE")
        self.assertEqual(envelopes[0]["section_profile"]["material_volume_mm3"], "0", "Q38JA_ENVELOPE")
        for obj in objects:
            detail = obj["section_profile"]
            self.assertEqual(obj["root"], {"kind": "profile-run", "id": 1})
            self.assertEqual(detail["coordinate_space"], "world")
            if obj["role"] == "geometry":
                member_id = detail["member_id"]
                actual = [[min(p[i] for p in obj["vertices_mm"]) for i in range(3)],
                          [max(p[i] for p in obj["vertices_mm"]) for i in range(3)]]
                self.assertEqual(actual, BOXES[member_id], "Q38JA_EXACT_BOX")
                self.assertEqual(obj["member_path"], [member_id])
                self.assertEqual(detail["dimensions_mm"], [27, 33, 2400])
                self.assertEqual(detail["material_volume_mm3"], "2138400", "Q38JA_MATERIAL")
                self.assertEqual(profiles.signed_volume6(obj), 6 * 2138400, "Q38JA_EXACT_MESH")
        summary = result["summary"]
        self.assertEqual(summary["profile_run_count"], 1)
        self.assertEqual(summary["profile_member_count"], 3, "Q38JA_MATERIAL")
        self.assertEqual(summary["profile_material_volume_mm3"], "6415200", "Q38JA_MATERIAL")
        self.assertIs(summary["profile_overlap_checked"], False, "Q38JA_OVERLAP")

    def test_q01b_all_selected_roots_are_sorted_in_one_request(self):
        with mock.patch.object(sm, "build_package", wraps=sm.build_package) as build:
            result = self.preview(f1(ids=(4, 1)))
        calls = [call for call in build.call_args_list if call.args[1]["roots"][0]["kind"] == "profile-run"]
        self.assertEqual(len(calls), 1, "Q38JA_SINGLE_REQUEST")
        self.assertEqual(calls[0].args[1], {"roots": [{"kind": "profile-run", "id": 1}, {"kind": "profile-run", "id": 4}],
                                          "role": "geometry", "target": "solid-set", "allow_partial": False}, "Q38JA_ROOT_ORDER")
        self.assertEqual(result["summary"]["profile_run_count"], 2)
        self.assertEqual(result["summary"]["profile_member_count"], 6)
        self.assertEqual(result["summary"]["profile_material_volume_mm3"], "9088200", "Q38JA_OVERLAP")
        self.assertIs(result["summary"]["profile_overlap_checked"], False, "Q38JA_OVERLAP")

    def test_r430_native_source_receipt_keeps_raw_snapshot_and_canonical_source(self):
        data = f1(timber=True)
        canonical = load_base(data["base_scene"], executable=self.base)["base_scene"]
        data["base_scene"] = "# R430 editor annotation\n" + canonical + "canvas-pos boundary 1 60 60\n"
        result = self.preview(data)
        self.assertTrue("source_snapshot" in result, "R430_NATIVE_SOURCE_RECEIPT")
        receipt = result["source_snapshot"]
        self.assertEqual(receipt, {"schema": "geometry-space-source/1",
                                  "input_sha256": hashlib.sha256(data["base_scene"].encode()).hexdigest(),
                                  "canonical_scene": canonical}, "R430_NATIVE_SOURCE_RECEIPT")
        self.assertNotEqual(data["base_scene"], canonical, "R430_RAW_IS_NOT_CANONICAL")
        self.assertEqual(result["source_sha256"], hashlib.sha256(canonical.encode()).hexdigest(), "R430_CANONICAL_HASH")
        for key in ("profile_runs", "timbers"):
            self.assertEqual(result[key]["definitions"]["base_scene"], canonical, "R430_ONE_NATIVE_SOURCE")
        for key in ("space", "volume", "clearance", "walls"):
            lines = result[key]["definitions"]["base_scene"].splitlines()
            self.assertTrue(all(lines.count(line) == 1 for line in canonical.splitlines()), "R430_ONE_NATIVE_SOURCE")
        self.assertEqual(sm.replay_stored(data, result, base_executable=self.base), result)
        # Even a metadata-only change denotes a different saved input snapshot.
        changed = deepcopy(data)
        changed["base_scene"] = changed["base_scene"].replace("60 60", "61 60")
        with self.assertRaises(ModelError, msg="R430_RAW_REPLAY_BINDING") as caught:
            sm.replay_stored(changed, result, base_executable=self.base)
        self.assertEqual(caught.exception.code, "SPACE_STORED_REPLAY", "R430_RAW_REPLAY_BINDING")
        forged = deepcopy(result)
        forged["source_snapshot"]["canonical_scene"] = canonical.replace("4000,0", "4100,0")
        with self.assertRaises(ModelError, msg="R430_CANONICAL_REPLAY_BINDING"):
            sm.replay_stored(data, forged, base_executable=self.base)

    def test_q02_q17_omitted_selection_keeps_schema1_and_existing_packages_exact(self):
        plain = self.preview(f1(ids=None))
        included = self.preview(f1())
        self.assertEqual(plain["schema"], "geometry-space-preview/1")
        self.assertNotIn("profile_runs", plain)
        self.assertFalse(PROFILE_SUMMARY & plain["summary"].keys())
        for key in ("space", "volume", "clearance", "walls", "source_sha256", "diagnostics"):
            self.assertEqual(canonical_bytes(included[key]), canonical_bytes(plain[key]), "Q38JA_NO_CROSS_TOTAL:" + key)
        self.assertEqual({k: v for k, v in included["summary"].items() if k not in PROFILE_SUMMARY}, plain["summary"], "Q38JA_NO_CROSS_TOTAL")
        self.assertEqual(included["summary"]["volume_mm3"], "54000000000")

    def test_q19_schema3_coexists_with_unchanged_schema2_timbers(self):
        old = self.preview(f1(ids=None, timber=True))
        new = self.preview(f1(timber=True))
        self.assertEqual(old["schema"], "geometry-space-preview/2")
        self.assertEqual(new["schema"], "geometry-space-preview/3")
        self.assertEqual(canonical_bytes(new["timbers"]), canonical_bytes(old["timbers"]), "Q38JA_TIMBERS")
        self.assertEqual({k: v for k, v in new["summary"].items() if k not in PROFILE_SUMMARY}, old["summary"], "Q38JA_TIMBERS")
        self.assertEqual(new["summary"]["timber_volume_mm3"], "3564000")

    def test_q03_unlocated_member_has_d39_path_and_no_partial_result(self):
        exc = self.reject(f1(ids=(1, 2)), "SPACE_PROFILE_RUNS", marker="Q38JA_LOCAL")
        self.assertEqual(exc.clause, "D39", "Q38JA_LOCAL")
        self.assertEqual(exc.path, ["profile_runs", 1])
        self.assertIn("#2", exc.message)

    def test_q04_empty_selection_instructs_omission(self):
        exc = self.reject(f1(ids=()), "SPACE_PROFILE_RUNS", marker="Q38JA_EMPTY")
        self.assertIn("省略", exc.message)

    def test_q04_strict_typed_unique_uint32_selection(self):
        cases = [None, {}, "1", [{"kind": "profile-run", "id": 1}] * 2,
                 [{"kind": "profile-run", "id": 999}], [{"kind": "timber", "id": 1}],
                 *[[{"kind": "profile-run", "id": bad}] for bad in (-1, True, "1", 0x100000000)]]
        for refs in cases:
            with self.subTest(refs=refs):
                data = f1(); data["profile_runs"] = refs
                self.reject(data, "SPACE_PROFILE_RUNS")
        data = f1(); data["profile_runs"] = [{"kind": "profile-run", "id": 1.5}]
        self.reject(data, "JSON_TYPE")
        for refs in ([{}], [{"kind": "profile-run", "id": 1, "extra": 0}]):
            with self.subTest(refs=refs):
                data = f1(); data["profile_runs"] = refs
                self.reject(data)

    def test_q04_zero_id_is_an_explicit_native_root(self):
        try:
            result = self.preview(f1(ids=(0,)))
        except ModelError as exc:
            self.fail("Q38JA_ZERO_ID: " + exc.code)
        self.assertEqual(result["profile_runs"]["request"]["roots"], [{"kind": "profile-run", "id": 0}], "Q38JA_ZERO_ID")
        self.assertEqual(result["summary"]["profile_material_volume_mm3"], "6415200")

    def test_q01_zero_member_id_and_empty_profile_preserve_native_semantics(self):
        for members in ([profiles.member(0)], []):
            data = f1()
            data["base_scene"] = profiles.scene(prefix=PREFIX, members=members,
                                               runs=[profiles.run(placement=deepcopy(FRAME))])
            with self.subTest(members=len(members)):
                result = self.preview(data)
                self.assertEqual(result["summary"]["profile_member_count"], len(members))
                self.assertEqual(result["summary"]["profile_material_volume_mm3"], "2138400" if members else "0")
                objects = result["profile_runs"]["derived"]["objects"]
                self.assertEqual(len(objects), len(members) + 1)
                self.assertEqual([o["member_path"] for o in objects if o["role"] == "geometry"], [[0]] if members else [])

    def test_q15_faces_rejects_profile_selection_explicitly(self):
        data = {"mode": "faces", "base_scene": f1()["base_scene"], "obstacles": [],
                "uses": [{"placement_id": 1, "orientation": 1, "purpose": "boundary"}],
                "profile_runs": [{"kind": "profile-run", "id": 1}]}
        self.reject(data, "SPACE_PROFILE_RUNS_MODE", status="UNSUPPORTED", marker="Q38JA_FACES")

    def test_q05_native_failure_preserves_status_diagnostic_and_rejects_whole_preview(self):
        original = sm.build_package
        for status in ("UNSUPPORTED", "INVALID", "INCOMPLETE"):
            def injected(definitions, request, **options):
                if request["roots"][0]["kind"] == "profile-run":
                    raise ModelError(status, "CAPACITY", "I33", "native capacity", path=["members", 3],
                                     root={"kind": "profile-run", "id": 4})
                return original(definitions, request, **options)
            with self.subTest(status=status), mock.patch.object(sm, "build_package", side_effect=injected):
                exc = self.reject(f1(ids=(4, 1)), "CAPACITY", status=status, marker="Q38JA_ALL_OR_NONE")
                self.assertEqual(exc.path, ["profile_runs", "members", 3], "Q38JA_ALL_OR_NONE")
                self.assertEqual(exc.root, {"kind": "profile-run", "id": 4})
                self.assertIn("#1", exc.message)
                self.assertIn("#4", exc.message)
                self.assertTrue(exc.diagnostics)
                self.assertEqual(exc.diagnostics[0]["path"], ["profile_runs", "members", 3])

    def corrupt_package(self, change, marker):
        data = f1()
        good = self.preview(data)["profile_runs"]
        bad = deepcopy(good)
        change(bad)
        original_build, original_verify = sm.build_package, sm.verify_package
        def build(definitions, request, **options):
            return deepcopy(bad) if request["roots"][0]["kind"] == "profile-run" else original_build(definitions, request, **options)
        def verify(package, **options):
            # Exercise the host's independent completeness boundary, after the
            # native package and generic replay have already been tested above.
            return package if package["request"]["roots"][0]["kind"] == "profile-run" else original_verify(package, **options)
        with mock.patch.object(sm, "build_package", side_effect=build), mock.patch.object(sm, "verify_package", side_effect=verify):
            self.reject(data, "SPACE_PROFILE_RUNS_INCOMPLETE", marker=marker)

    def test_q08_envelope_must_be_one_zero_material_reference_per_run(self):
        def envelope_material(package):
            obj = next(o for o in package["derived"]["objects"] if o["role"] == "reference")
            obj["section_profile"]["material_volume_mm3"] = obj["volume_mm3"]
        self.corrupt_package(envelope_material, "Q38JA_ENVELOPE_GUARD")
        self.corrupt_package(lambda p: p["derived"].update(objects=[o for o in p["derived"]["objects"] if o["role"] != "reference"]), "Q38JA_ENVELOPE_GUARD")

    def test_q08_missing_member_is_never_partial_success(self):
        self.corrupt_package(lambda p: p["derived"]["objects"].pop(), "Q38JA_MEMBER_CLOSURE")

    def test_q08_package_world_identity_dimensions_and_source_guards(self):
        def geometry(package):
            return next(o for o in package["derived"]["objects"] if o["role"] == "geometry")
        changes = [lambda p: p["definitions"].update(base_scene=""),
                   lambda p: p["request"].update(allow_partial=True),
                   lambda p: p["derived"].update(status="INCOMPLETE"),
                   lambda p: geometry(p)["section_profile"].update(coordinate_space="local"),
                   lambda p: geometry(p).update(member_path=[999]),
                   lambda p: geometry(p)["section_profile"].update(material_volume_mm3="1"),
                   lambda p: geometry(p)["section_profile"].update(dimensions_mm=[27, 33, True])]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                self.corrupt_package(change, "Q38JA_PACKAGE_GUARD")

    def test_q07_copied_wall_values_remain_fixed_when_model_height_changes(self):
        data = f1(copied=True)
        old = self.preview(data)
        data["settings"]["height"] = 3000
        new = self.preview(data)
        self.assertEqual(new["summary"]["top"], 3000)
        self.assertEqual(canonical_bytes(new["profile_runs"]), canonical_bytes(old["profile_runs"]), "Q38JA_COPIED_FRAME")
        materials = [o for o in new["profile_runs"]["derived"]["objects"] if o["role"] == "geometry"]
        for obj in materials:
            self.assertEqual(obj["section_profile"]["bounds_mm"], BOXES[obj["section_profile"]["member_id"]], "Q38JA_COPIED_FRAME")

    def test_q08_model_replay_rejects_self_consistent_foreign_snapshot(self):
        data = f1(); original = self.preview(data)
        foreign = self.preview(f1(length=2000))["profile_runs"]
        self.assertEqual(verify_package(foreign, base_executable=self.base), foreign)
        corrupted = deepcopy(original); corrupted["profile_runs"] = foreign
        with self.assertRaises(ModelError, msg="Q38JA_MODEL_SOURCE_REPLAY") as caught:
            sm.replay_stored(data, corrupted, base_executable=self.base)
        self.assertEqual(caught.exception.code, "SPACE_STORED_REPLAY", "Q38JA_MODEL_SOURCE_REPLAY")
        self.assertEqual(sm.replay_stored(data, original, base_executable=self.base), original)

    def test_q08_model_replay_validates_original_profile_manifest(self):
        data = f1(); result = self.preview(data)
        result["profile_runs"]["manifest"]["generator"] = {"name": "q38j-archival-generator", "version": "1"}
        # Generator is archival provenance, not geometric semantics. Rebuilding
        # with today's generator must not overwrite a conforming older record.
        verify_package(result["profile_runs"], base_executable=self.base)
        try:
            replayed = sm.replay_stored(data, result, base_executable=self.base)
        except ModelError as exc:
            self.fail("Q38JA_REPLAY_PROVENANCE: conforming archival provenance rejected: " + exc.code)
        self.assertEqual(replayed, result, "Q38JA_REPLAY_PROVENANCE")
        result["profile_runs"]["manifest"]["source_sha256"] = "0" * 64
        with self.assertRaises(ModelError, msg="Q38JA_MODEL_MANIFEST_REPLAY"):
            sm.replay_stored(data, result, base_executable=self.base)

    def test_q08f_scenario_replay_rejects_self_consistent_foreign_profile_package(self):
        data = f1(); result = self.preview(data); record = saved_record(data, result)
        self.assertIn("section-profile/1", scenario_verify._model(record, self.base, 0))
        foreign = self.preview(f1(length=2000))["profile_runs"]
        self.assertEqual(verify_package(foreign, base_executable=self.base), foreign)
        record["result"]["profile_runs"] = foreign
        before = canonical_bytes(record)
        with self.assertRaises(ModelError, msg="Q38JA_SCENARIO_PROFILE_REPLAY") as caught:
            scenario_verify._model(record, self.base, 0)
        self.assertEqual(caught.exception.code, "SCENARIO_MODEL_REPLAY", "Q38JA_SCENARIO_PROFILE_REPLAY")
        self.assertEqual(canonical_bytes(record), before)

    def test_r430_scenario_replay_rejects_forged_source_receipt(self):
        data = f1()
        record = saved_record(data, self.preview(data))
        record["result"]["source_snapshot"]["input_sha256"] = "a" * 64
        before = canonical_bytes(record)
        with self.assertRaises(ModelError, msg="R430_SCENARIO_SOURCE_RECEIPT") as caught:
            scenario_verify._model(record, self.base, 0)
        self.assertEqual(caught.exception.code, "SCENARIO_MODEL_REPLAY", "R430_SCENARIO_SOURCE_RECEIPT")
        self.assertEqual(canonical_bytes(record), before)

    def test_q08f_schema3_scenario_still_verifies_original_timber_package(self):
        data = f1(timber=True); record = saved_record(data, self.preview(data))
        scenario_verify._model(record, self.base, 0)
        changed = f1(timber=True)
        changed["base_scene"] = changed["base_scene"].replace("timber 0 27 33", "timber 0 29 33")
        record["result"]["timbers"] = self.preview(changed)["timbers"]
        with self.assertRaises(ModelError, msg="Q38JA_SCENARIO_TIMBER_REPLAY") as caught:
            scenario_verify._model(record, self.base, 0)
        self.assertEqual(caught.exception.code, "SCENARIO_MODEL_REPLAY", "Q38JA_SCENARIO_TIMBER_REPLAY")

    def test_q08_summary_material_overlap_and_selection_tamper_reject(self):
        data = f1(); result = self.preview(data)
        for key, value in (("profile_material_volume_mm3", "91375200"), ("profile_overlap_checked", True),
                           ("profile_member_count", 4), ("profile_run_count", 2)):
            corrupt = deepcopy(result); corrupt["summary"][key] = value
            with self.subTest(key=key), self.assertRaises(ModelError, msg="Q38JA_SUMMARY_REPLAY"):
                sm.replay_stored(data, corrupt, base_executable=self.base)
        other = f1(ids=(0,))
        with self.assertRaises(ModelError, msg="Q38JA_SELECTION_REPLAY"):
            sm.replay_stored(other, result, base_executable=self.base)

    def test_q21c_f1b_requires_explicit_profile_selection(self):
        data = f1(); record = saved_record(data, self.preview(data))
        request = {"record": record, "current_scene": data["base_scene"],
                   "selection": {"placement_id": 1, "boundary_id": 1, "edges": [0, 1, 2, 3],
                                 "obstacles": [], "timbers": [], "projection": None}}
        before = canonical_bytes(request)
        with self.assertRaises(ModelError, msg="Q38JC_EXPLICIT_SELECTION") as caught:
            model_update.prepare_update(request, base_executable=self.base)
        self.assertEqual((caught.exception.status, caught.exception.code), ("INVALID", "UPDATE_SHAPE"), "Q38JC_EXPLICIT_SELECTION")
        self.assertEqual(canonical_bytes(request), before)


if __name__ == "__main__":
    unittest.main()
