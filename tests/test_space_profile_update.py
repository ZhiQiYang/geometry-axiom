"""Q38j-c F1b: native replacements and the current K3 covered-root boundary.

The isolated producer returns content-only candidate/1; the App preserves its
existing K3 candidate/2 pin confirmation. Profile runs never acquire K3 pins.
"""
import base64
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "geometry-web", ROOT / "geometry-core"):
    sys.path.insert(0, str(directory))
from tests import _bridge, binaries
from tests.test_space_profile_runs import PREFIX, f1, saved_record
from tests.test_section_profile_modeling import literal, record as profile_line
import model_update as update
import scenario_verify
import space_modeling as sm
from modeling import ModelError, canonical_bytes, verify_package
from modeling.base import load_base
from modeling.common import digest


def change_profile(source, kind, identifier, mutate):
    lines = source.splitlines(keepends=True)
    found = False
    for index, line in enumerate(lines):
        if not line.startswith("section-profile " + kind + " "):
            continue
        value = json.loads(base64.b64decode(line.split()[2]))
        if value["id"] == identifier:
            mutate(value)
            lines[index] = profile_line(kind, value)
            found = True
    if not found:
        raise AssertionError("fixture profile record not found")
    return "".join(lines)


class SpaceProfileUpdate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _bridge.find_bridge()
        info = binaries.inspect_one(binaries.BY_NAME["model-base"], path=os.environ.get("GEOMETRY_MODEL_BASE"))
        if info.state != "fresh":
            raise unittest.SkipTest("Set GEOMETRY_MODEL_BASE to a fresh adapter: " + info.reason)
        cls.base = str(info.path)
        cls.native = {"base_executable": cls.base, "bridge_executable": cls.bridge}
        inputs = f1(timber=True)
        inputs["base_scene"] = load_base(inputs["base_scene"], executable=cls.base)["base_scene"]
        cls.old = saved_record(inputs, sm.preview(inputs, base_executable=cls.base))

    def record(self, source, *, selected=(1,)):
        inputs = f1(ids=selected, timber=True)
        inputs["base_scene"] = load_base(source, executable=self.base)["base_scene"]
        return saved_record(inputs, sm.preview(inputs, base_executable=self.base))

    def request(self, *, old=None, source=None, selected=(1,)):
        old = deepcopy(self.old if old is None else old)
        return {"record": old, "current_scene": source or old["input"]["base_scene"],
                "selection": {"placement_id": 1, "boundary_id": 1, "edges": [0, 1, 2, 3],
                              "obstacles": [], "timbers": [{"kind": "timber", "id": 0}],
                              "profile_runs": [{"kind": "profile-run", "id": identifier} for identifier in selected],
                              "projection": None}}

    def prepare(self, data, marker="Q38JC_PRODUCER"):
        before = canonical_bytes(data)
        try:
            result = update.prepare_update(data, **self.native)
        except ModelError as error:
            self.fail(marker + ": expected complete replacement, got " + error.code)
        self.assertEqual(canonical_bytes(data), before, "Q38JC_INPUT_UNCHANGED")
        return result

    def refuse(self, data, code, marker):
        before = canonical_bytes(data)
        with self.assertRaises(ModelError, msg=marker) as caught:
            update.prepare_update(data, **self.native)
        self.assertEqual(caught.exception.code, code, marker)
        self.assertEqual(canonical_bytes(data), before, "Q38JC_REJECT_UNCHANGED")
        return caught.exception

    def test_q20_add_copied_run_rebuilds_every_package_from_one_current_source(self):
        old = self.record(self.old["input"]["base_scene"], selected=None)
        copied = [json.loads(base64.b64decode(line.split()[2]))
                  for line in f1(copied=True, timber=True)["base_scene"].splitlines()
                  if line.startswith("section-profile run ")]
        run3 = next(value for value in copied if value["id"] == 1)
        run3["id"] = 3
        current = old["input"]["base_scene"] + profile_line("run", run3)
        data = self.request(old=old, source=current, selected=(3,))
        candidate = self.prepare(data, "Q38JC_ADD")
        result, replacement = candidate["record"]["result"], candidate["record"]
        self.assertEqual(replacement["id"], old["id"], "Q38JC_SAME_MODEL_ID")
        self.assertEqual(candidate["identity"], "unknown", "Q38JC_NO_INVENTED_IDENTITY")
        self.assertEqual(candidate["schema"], "geometry-model-update-candidate/1")
        self.assertNotIn("sourceIdentity", replacement)
        self.assertNotEqual(replacement["input"]["base_scene"], old["input"]["base_scene"], "Q38JC_FULL_SOURCE")
        self.assertEqual(result["schema"], "geometry-space-preview/3", "Q38JC_ADD")
        self.assertEqual(result["summary"]["profile_material_volume_mm3"], "6415200", "Q38JC_ADD")
        self.assertEqual(replacement["input"]["profile_runs"], data["selection"]["profile_runs"])
        self.assertEqual(result["profile_runs"]["definitions"]["base_scene"], replacement["input"]["base_scene"], "Q38JC_FULL_SOURCE")
        self.assertEqual(result["source_sha256"], hashlib.sha256(replacement["input"]["base_scene"].encode()).hexdigest())
        expected_packages = ["space", "volume", "clearance", "walls", "timbers", "profile_runs"]
        self.assertEqual([row["kind"] for row in candidate["diff"]["packages"]], expected_packages, "Q38JC_DIFF_PACKAGES")
        for key in expected_packages:
            self.assertEqual(verify_package(result[key], base_executable=self.base), result[key])
            if key != "profile_runs":
                self.assertNotEqual(result[key]["definitions"], old["result"][key]["definitions"], "Q38JC_REBUILD_ALL")
        row = next(row for row in candidate["diff"]["packages"] if row["kind"] == "profile_runs")
        self.assertEqual(row, {"kind":"profile_runs", "before":None, "after":digest(result["profile_runs"]["manifest"])})
        for obj in result["profile_runs"]["derived"]["objects"]:
            if obj["role"] == "geometry":
                self.assertEqual(obj["section_profile"]["bounds_mm"][0][2], 2450 if obj["section_profile"]["member_id"] == 3 else 2667)

    def test_q21_explicit_empty_removes_profile_package_without_old_fallback(self):
        data = self.request(selected=())
        replacement = self.prepare(data, "Q38JC_REMOVE")["record"]
        self.assertEqual(replacement["id"], self.old["id"])
        self.assertNotIn("profile_runs", replacement["input"], "Q38JC_REMOVE")
        self.assertNotIn("profile_runs", replacement["result"], "Q38JC_REMOVE")
        self.assertEqual(replacement["result"]["schema"], "geometry-space-preview/2", "Q38JC_REMOVE")
        self.assertEqual(replacement["result"]["timbers"], self.old["result"]["timbers"])
        self.assertFalse(any(key.startswith("profile_") for key in replacement["result"]["summary"]))

    def test_q21_selection_is_required_typed_unique_and_never_inferred(self):
        missing = self.request(); del missing["selection"]["profile_runs"]
        self.refuse(missing, "UPDATE_SHAPE", "Q38JC_EXPLICIT_SELECTION")
        cases = [(None, "UPDATE_SELECTION"), ({}, "UPDATE_SELECTION"),
                 ([{"kind":"timber","id":1}], "UPDATE_SELECTION"),
                 ([{"kind":"profile-run","id":True}], "UPDATE_ID"),
                 ([{"kind":"profile-run","id":-1}], "UPDATE_ID"),
                 ([{"kind":"profile-run","id":1}]*2, "UPDATE_SELECTION")]
        for bad, expected in cases:
            data = self.request(); data["selection"]["profile_runs"] = bad
            self.refuse(data, expected, "Q38JC_SELECTION")

    def test_q21_zero_run_is_selected_and_unlocated_or_missing_fails_atomically(self):
        replacement = self.prepare(self.request(selected=(0,)), "Q38JC_ZERO_RUN")["record"]
        self.assertEqual(replacement["input"]["profile_runs"], [{"kind":"profile-run","id":0}], "Q38JC_ZERO_RUN")
        self.assertEqual(replacement["result"]["profile_runs"]["request"]["roots"], [{"kind":"profile-run","id":0}])
        self.refuse(self.request(selected=(2,)), "SPACE_PROFILE_RUNS", "Q38JC_LOCAL_RUN")
        self.refuse(self.request(selected=(999,)), "UPDATE_GRAPH_UNCHECKED", "Q38JC_MISSING_RUN")

    def test_q20_same_run_length_change_rebuilds_new_model_but_preserves_old_record(self):
        changed = change_profile(self.old["input"]["base_scene"], "run", 1, lambda value:value.update(length=literal(2000)))
        data = self.request(source=changed)
        replacement = self.prepare(data, "Q38JC_CURRENT_LENGTH")["record"]
        self.assertEqual(replacement["result"]["summary"]["profile_material_volume_mm3"], "5346000", "Q38JC_CURRENT_LENGTH")
        self.assertEqual(self.old["result"]["summary"]["profile_material_volume_mm3"], "6415200")
        self.assertEqual(sm.replay_stored(replacement["input"], replacement["result"], base_executable=self.base), replacement["result"])

    def test_q20_embedded_profile_source_retains_native_null_boundary_for_all_replays(self):
        inputs = f1()
        source = inputs["base_scene"].replace(PREFIX, "surface 0 origin 0 0 0 u +x v +y rect 0 0 4000 5000\n", 1)
        native = load_base(source, executable=self.base)
        self.assertIsNone(native["placements"][0]["boundary_id"])
        inputs.update(base_scene=native["base_scene"], placement_id=0)
        old = saved_record(inputs, sm.preview(inputs, base_executable=self.base))
        old["source"].update(placement_id=0, boundary_id=None)
        data = self.request(old=old)
        data["selection"].update(placement_id=0, boundary_id=0, timbers=[])
        replacement = self.prepare(data, "Q38JC_EMBEDDED_BOUNDARY")["record"]
        self.assertIsNone(replacement["source"]["boundary_id"], "Q38JC_EMBEDDED_BOUNDARY")
        self.assertEqual(replacement["result"]["schema"], "geometry-space-preview/3", "Q38JC_EMBEDDED_BOUNDARY")
        self.assertEqual(sm.replay_stored(replacement["input"], replacement["result"], base_executable=self.base), replacement["result"])
        self.assertIn("section-profile/1", scenario_verify._model(replacement, self.base, 0), "Q38JC_EMBEDDED_BOUNDARY")
        wrong = deepcopy(replacement)
        wrong["source"]["boundary_id"] = 0
        with self.assertRaises(ModelError, msg="Q38JC_EMBEDDED_BOUNDARY") as caught:
            scenario_verify._model(wrong, self.base, 0)
        self.assertEqual(caught.exception.code, "SCENARIO_MODEL_REPLAY", "Q38JC_EMBEDDED_BOUNDARY")
        invalid_old = deepcopy(data)
        invalid_old["record"] = wrong
        self.refuse(invalid_old, "UPDATE_SOURCE", "Q38JC_OLD_EMBEDDED_SOURCE")
        removal = deepcopy(data)
        removal["selection"]["profile_runs"] = []
        removed = self.prepare(removal, "Q38JC_EMBEDDED_REMOVE")["record"]
        self.assertIsNone(removed["source"]["boundary_id"], "Q38JC_EMBEDDED_REMOVE")
        self.assertEqual(removed["result"]["schema"], "geometry-space-preview/1", "Q38JC_EMBEDDED_REMOVE")
        self.assertNotIn("profile_runs", removed["input"], "Q38JC_EMBEDDED_REMOVE")
        self.assertNotIn("profile_runs", removed["result"], "Q38JC_EMBEDDED_REMOVE")
        self.assertEqual(sm.replay_stored(removed["input"], removed["result"], base_executable=self.base), removed["result"])
        self.assertIn("section-profile/1", scenario_verify._model(removed, self.base, 0), "Q38JC_EMBEDDED_REMOVE")
        continuation = deepcopy(removal)
        continuation["record"] = removed
        repeated = self.prepare(continuation, "Q38JC_EMBEDDED_CONTINUATION")["record"]
        self.assertIsNone(repeated["source"]["boundary_id"], "Q38JC_EMBEDDED_CONTINUATION")
        self.assertEqual(repeated, removed, "Q38JC_EMBEDDED_CONTINUATION")
        self.assertEqual(sm.replay_stored(repeated["input"], repeated["result"], base_executable=self.base), repeated["result"])
        self.assertIn("section-profile/1", scenario_verify._model(repeated, self.base, 0), "Q38JC_EMBEDDED_CONTINUATION")

    def material_scene(self, *, name="Fixed", swapped=False):
        source = self.old["input"]["base_scene"]
        materials = [{"id":"profile-wood", "version":version, "kind":"timber", "name":name if version == 1 else "Other", "A":27, "B":33} for version in (1,2)]
        catalogue = "requires engineering-spec/1\n" + "".join("engineering material " +
            base64.b64encode(canonical_bytes({"fingerprint":digest(value), "value":value})).decode() + "\n"
            for value in materials)
        def bind(value):
            value["A"] = {"kind":"material", "id":"profile-wood", "version":2 if swapped else 1, "field":"A"}
            value["B"] = {"kind":"material", "id":"profile-wood", "version":1 if swapped else 2, "field":"B"}
        return catalogue + change_profile(source, "member", 1, bind)

    def test_q22_same_material_version_changed_content_is_rejected_from_profile_closure(self):
        before = self.material_scene()
        old = self.record(before)
        changed = self.material_scene(name="Changed fixed version content")
        error = self.refuse(self.request(old=old, source=changed), "UPDATE_FIXED_VERSION", "Q38JC_FIXED_PROFILE_VERSION")
        self.assertEqual(error.status, "INVALID")
        self.assertTrue(any(row["id"] == "profile-wood" for row in error.diagnostics[0]["missing"]["before_only"]))

    def test_q22_equal_value_A_B_fixed_reference_swap_is_rejected_per_member_field(self):
        old = self.record(self.material_scene())
        self.refuse(self.request(old=old, source=self.material_scene(swapped=True)), "UPDATE_FIXED_VERSION", "Q38JC_FIXED_PROFILE_FIELDS")

    def test_q08_old_foreign_profile_package_cannot_be_updated_into_legitimacy(self):
        data = self.request()
        foreign = self.record(change_profile(self.old["input"]["base_scene"], "run", 1, lambda value:value.update(length=literal(2000))))
        data["record"]["result"]["profile_runs"] = foreign["result"]["profile_runs"]
        self.refuse(data, "UPDATE_OLD_REPLAY", "Q38JC_OLD_REPLAY")

    def covered_record(self):
        old = deepcopy(self.old)
        old["sourceIdentity"] = {"schema": "model-source-identity/1", "roots": [
            {"role": "placement", "kind": "placement", "id": 1, "incarnation": "a" * 32 + ":1"},
            {"role": "boundary", "kind": "boundary", "id": 1, "incarnation": "a" * 32 + ":2"},
            {"role": "timber", "kind": "timber", "id": 0, "incarnation": "a" * 32 + ":3"}]}
        return old

    def test_qk03_covered_identity_and_profile_model_use_same_strict_replay_roots(self):
        old = self.covered_record()
        candidate = self.prepare(self.request(old=old), "Q38JK_COVERED_UPDATE")
        self.assertEqual(candidate["record"]["result"], old["result"], "Q38JK_COVERED_UPDATE")
        self.assertNotIn("sourceIdentity", candidate["record"], "Q38JK_NO_INVENTED_PIN")
        try:
            required = scenario_verify._model(old, self.base, 0)
        except ModelError as exc:
            self.fail("Q38JK_COVERED_REPLAY: valid covered roots rejected: " + exc.code)
        self.assertIn("section-profile/1", required, "Q38JK_COVERED_REPLAY")

    def test_qk02_profile_pin_or_uncovered_reason_never_enters_covered_identity(self):
        for extra in (
            {"role": "profile-run", "kind": "profile-run", "id": 1, "incarnation": "a" * 32 + ":4"},
            {"role": "profile-run", "kind": "profile-run", "id": 1, "incarnation": None, "uncovered": "profile-run"},
        ):
            old = self.covered_record()
            old["sourceIdentity"]["roots"].append(extra)
            with self.subTest(extra=extra):
                self.refuse(self.request(old=old), "UPDATE_IDENTITY", "Q38JK_PROFILE_PIN")
                with self.assertRaises(ModelError, msg="Q38JK_SCENARIO_PROFILE_PIN") as caught:
                    scenario_verify._model(old, self.base, 0)
                self.assertEqual(caught.exception.code, "SCENARIO_MODEL_IDENTITY", "Q38JK_SCENARIO_PROFILE_PIN")

    def test_qk03_original_covered_pins_cannot_be_dropped_because_runs_are_untracked(self):
        old = self.covered_record()
        old["sourceIdentity"]["roots"].pop()
        self.refuse(self.request(old=old), "UPDATE_IDENTITY", "Q38JK_COVERED_ROOTS")
        with self.assertRaises(ModelError, msg="Q38JK_SCENARIO_COVERED_ROOTS") as caught:
            scenario_verify._model(old, self.base, 0)
        self.assertEqual(caught.exception.code, "SCENARIO_MODEL_IDENTITY", "Q38JK_SCENARIO_COVERED_ROOTS")


if __name__ == "__main__":
    unittest.main()
